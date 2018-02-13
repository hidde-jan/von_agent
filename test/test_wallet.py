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

from von_agent.nodepool import NodePool
from von_agent.wallet import Wallet

import pytest


#noinspection PyUnusedLocal
@pytest.mark.asyncio
async def test_wallet(
    pool_name,
    pool_genesis_txn_path,
    pool_genesis_txn_file):

    p = NodePool(pool_name, pool_genesis_txn_path, {'auto_remove': True})
    seed = '00000000000000000000000000000000'
    name = 'my-wallet'
    w = Wallet(p.name, name)

    await w.open()
    await w.create_did(seed=seed)
    assert w.did
    assert w.verkey
    (did, verkey) = (w.did, w.verkey)
    await w.close()

    x = Wallet(p.name, name)
    await x.open()
    await x.create_did(seed=seed)
    assert did == x.did
    assert verkey == x.verkey

    await x.close()

#noinspection PyUnusedLocal
@pytest.mark.asyncio
async def test_wallet_did_creation(
    pool_name,
    pool_genesis_txn_path,
    pool_genesis_txn_file):

    p = NodePool(pool_name, pool_genesis_txn_path, {'auto_remove': True})
    seed1 = '00000000000000000000000000000000'
    seed2 = '11111111111111111111111111111111'
    name = 'my-wallet'
    w = Wallet(p.name, name)

    await w.open()
    await w.create_did(seed=seed1)
    assert w.did
    assert w.verkey
    (did1, verkey1) = (w.did, w.verkey)
    await w.create_did(seed=seed2)
    (did2, verkey2) = (w.did, w.verkey)
    stored_dids = await w.stored_dids()

    assert len(stored_dids) == 2
    assert stored_dids[0]['did'] == did1
    assert stored_dids[0]['verkey'] == verkey1
    assert stored_dids[1]['did'] == did2
    assert stored_dids[1]['verkey'] == verkey2

    await w.close()

@pytest.mark.asyncio
async def test_wallet_did_loading(
    pool_name,
    pool_genesis_txn_path,
    pool_genesis_txn_file):

    p = NodePool(pool_name, pool_genesis_txn_path, {'auto_remove': True})
    seed1 = '00000000000000000000000000000000'
    seed2 = '11111111111111111111111111111111'
    name = 'my-wallet'
    w = Wallet(p.name, name)

    await w.open()
    await w.create_did(seed=seed1)
    assert w.did
    assert w.verkey
    (did1, verkey1) = (w.did, w.verkey)
    await w.create_did(seed=seed2)

    assert w.did != did1
    assert w.verkey != verkey1

    await w.load_did(did1)

    assert w.did == did1
    assert w.verkey == verkey1

    await w.close()
