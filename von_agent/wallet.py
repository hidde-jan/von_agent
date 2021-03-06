"""
Copyright 2017-2018 Government of Canada - Public Services and Procurement Canada - buyandsell.gc.ca

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from indy import did as indy_did
from indy import wallet, IndyError
from indy.error import ErrorCode

import json
import logging

logger = logging.getLogger(__name__)

class Wallet:
    """
    Class encapsulating indy-sdk wallet.
    """

    def __init__(self, pool_name: str, name: str, cfg: dict = None) -> None:
        """
        Initializer for wallet. Store input parameters and create wallet.
        Does not open until open() or __enter__().

        :param pool_name: name of pool on which wallet operates
        :param name: name of the wallet
        :param cfg: configuration, None for default;
            i.e., {
                'auto_remove': bool (default False), whether to remove serialized indy configuration data on close,
                ... (any other indy configuration data)
            }
        """

        logger.debug('Wallet.__init__: >>> pool_name {}, seed [SEED], name {}, cfg {}'.format(pool_name, name, cfg))

        self._pool_name = pool_name
        self._name = name
        self._handle = None
        self._cfg = cfg or {}

        self._did = None
        self._verkey = None

        logger.debug('Wallet.__init__: <<<')

    @property
    def pool_name(self) -> str:
        """
        Accessor for pool name.

        :return: pool name
        """

        return self._pool_name

    @property
    def name(self) -> str:
        """
        Accessor for wallet name.

        :return: wallet name
        """

        return self._name

    @property
    def handle(self) -> int:
        """
        Accessor for indy-sdk wallet handle.

        :return: indy-sdk wallet handle
        """

        return self._handle

    @property
    def cfg(self) -> dict:
        """
        Accessor for wallet config.

        :return: wallet config
        """

        return self._cfg

    @property
    def did(self) -> str:
        """
        Accessor for wallet DID.

        :return: wallet DID
        """

        return self._did

    @property
    def verkey(self) -> str:
        """
        Accessor for wallet verification key.

        :return: wallet verification key
        """

        return self._verkey

    async def __aenter__(self) -> 'Wallet':
        """
        Context manager entry. Create and open wallet as configured, for closure on context manager exit.
        For use in monolithic call opening, using, and closing wallet.

        :return: current object
        """

        logger = logging.getLogger(__name__)
        logger.debug('Wallet.__aenter__: >>>')

        rv = await self.open()
        logger.debug('Wallet.__aenter__: <<<')
        return rv

    async def open(self) -> 'Wallet':
        """
        Explicit entry. Open wallet as configured, for later closure via close().
        For use when keeping wallet open across multiple calls.

        :return: current object
        """

        logger = logging.getLogger(__name__)
        logger.debug('Wallet.open: >>>')

        cfg = json.loads(json.dumps(self._cfg))  # deep copy
        if 'auto_remove' in cfg:
            cfg.pop('auto_remove')

        try:
            await wallet.create_wallet(
                pool_name=self.pool_name,
                name=self.name,
                xtype=None,
                config=json.dumps(cfg) if cfg else None,
                credentials=None)
            logger.info('Created wallet {} on handle {}'.format(self.name, self.handle))
        except IndyError as e:
            if e.error_code == ErrorCode.WalletAlreadyExistsError:
                logger.info('Opening existing wallet: {}'.format(self.name))
            else:
                logger.error('Cannot open wallet {}: indy error code {}'.format(self.name, self.e.error_code))
                raise

        self._handle = await wallet.open_wallet(self.name, json.dumps(cfg) if cfg else None, None)
        logger.info('Opened wallet {} on handle {}'.format(self.name, self.handle))

        logger.debug('Wallet.open: <<<')
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None: 
        """
        Context manager exit. Close wallet and delete if so configured.
        For use in monolithic call opening, using, and closing the wallet.

        :param exc_type:
        :param exc:
        :param traceback:
        """

        logger = logging.getLogger(__name__)
        logger.debug('Wallet.__aexit__: >>>')

        await self.close()

        logger.debug('Wallet.__aexit__: <<<')

    async def close(self) -> None:
        """
        Explicit exit. Close and delete wallet.
        For use when keeping wallet open across multiple calls.
        """

        logger = logging.getLogger(__name__)
        logger.debug('Wallet.close: >>>')

        await wallet.close_wallet(self.handle)
        auto_remove = self.cfg.get('auto_remove', False)
        if auto_remove:
            await self.remove()

        logger.debug('Wallet.close: <<<')

    async def remove(self) -> None:
        """
        Remove serialized wallet configuration data if it exists.
        """

        logger = logging.getLogger(__name__)
        logger.debug('Wallet.close: >>>')

        try:
            await wallet.delete_wallet(self.name, None)
        except Exception:
            logger.info('Abstaining from wallet removal: {}'.format(sys.exc_info()[0]))

        logger.debug('Wallet.close: <<<')

    async def create_did(self, did: str=None, seed: str=None, cid: bool=False) -> str:
        identity_config = {"did": did, "seed": seed, "cid": cid}

        (self._did, self._verkey) = await indy_did.create_and_store_my_did(
            self._handle,
            json.dumps(identity_config))
        logger.debug('Wallet.create_did: stored {}, {}'.format(self._did, self._verkey))

        return self._did

    async def load_did(self, did: str) -> str:
        did_json = await indy_did.get_my_did_with_meta(self._handle, did)
        logger.debug('Wallet.load: {}'.format(did_json))
        did_info = json.loads(did_json)

        self._did = did_info['did']
        self._verkey = did_info['verkey']

        return self._did

    async def stored_dids(self):
        did_json = await indy_did.list_my_dids_with_meta(self._handle)
        logger.debug('Wallet.stored_dids: {}'.format(did_json))

        return json.loads(did_json)


    def __repr__(self) -> str:
        """
        Return representation for current object.

        :return: representation for current object
        """
        
        return '{}({}, [SEED], {}, {})'.format(
            self.__class__.__name__,
            self.pool_name,
            self.name,
            self.cfg)
