# Copyright DataStax, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Fixtures specific to the non-core-side testing."""

from typing import Iterable
import pytest

from ..conftest import (
    DataAPICredentials,
    DataAPICredentialsInfo,
    async_fail_if_not_removed,
    sync_fail_if_not_removed,
    IS_ASTRA_DB,
    SECONDARY_NAMESPACE,
)

from astrapy import AsyncCollection, AsyncDatabase, Collection, DataAPIClient, Database
from astrapy.constants import VectorMetric

TEST_COLLECTION_INSTANCE_NAME = "test_coll_instance"
TEST_COLLECTION_NAME = "id_test_collection"


@pytest.fixture(scope="session")
def client(
    data_api_credentials_info: DataAPICredentialsInfo,
) -> Iterable[DataAPIClient]:
    env = data_api_credentials_info["environment"]
    client = DataAPIClient(environment=env)
    yield client


@pytest.fixture(scope="session")
def sync_database(
    data_api_credentials_kwargs: DataAPICredentials,
    data_api_credentials_info: DataAPICredentialsInfo,
    client: DataAPIClient,
) -> Iterable[Database]:
    database = client.get_database(
        data_api_credentials_kwargs["api_endpoint"],
        token=data_api_credentials_kwargs["token"],
        namespace=data_api_credentials_kwargs["namespace"],
    )

    if not IS_ASTRA_DB:
        # ensure keyspace(s) exist
        database_admin = database.get_database_admin()
        database_admin.create_namespace(data_api_credentials_kwargs["namespace"])
        if data_api_credentials_info["secondary_namespace"]:
            database_admin.create_namespace(
                data_api_credentials_info["secondary_namespace"]
            )

    yield database


@pytest.fixture(scope="function")
def async_database(
    sync_database: Database,
) -> Iterable[AsyncDatabase]:
    yield sync_database.to_async()


@pytest.fixture(scope="session")
def sync_collection_instance(
    data_api_credentials_kwargs: DataAPICredentials,
    sync_database: Database,
) -> Iterable[Collection]:
    """Just an instance of the class, no DB-level stuff."""
    yield sync_database.get_collection(TEST_COLLECTION_INSTANCE_NAME)


@pytest.fixture(scope="function")
def async_collection_instance(
    sync_collection_instance: Collection,
) -> Iterable[AsyncCollection]:
    """Just an instance of the class, no DB-level stuff."""
    yield sync_collection_instance.to_async()


@pytest.fixture(scope="session")
def sync_collection(
    data_api_credentials_kwargs: DataAPICredentials,
    sync_database: Database,
) -> Iterable[Collection]:
    """An actual collection on DB, in the main namespace"""
    collection = sync_database.create_collection(
        TEST_COLLECTION_NAME,
        dimension=2,
        metric=VectorMetric.COSINE,
        indexing={"deny": ["not_indexed"]},
    )
    yield collection

    sync_database.drop_collection(TEST_COLLECTION_NAME)


@pytest.fixture(scope="function")
def sync_empty_collection(sync_collection: Collection) -> Iterable[Collection]:
    """Emptied for each test function"""
    sync_collection.delete_many({})
    yield sync_collection


@pytest.fixture(scope="function")
def async_collection(
    sync_collection: Collection,
) -> Iterable[AsyncCollection]:
    """An actual collection on DB, the same as the sync counterpart"""
    yield sync_collection.to_async()


@pytest.fixture(scope="function")
def async_empty_collection(
    sync_empty_collection: Collection,
) -> Iterable[AsyncCollection]:
    """Emptied for each test function"""
    yield sync_empty_collection.to_async()


__all__ = [
    "DataAPICredentials",
    "DataAPICredentialsInfo",
    "sync_database",
    "sync_fail_if_not_removed",
    "async_database",
    "async_fail_if_not_removed",
    "IS_ASTRA_DB",
    "SECONDARY_NAMESPACE",
]
