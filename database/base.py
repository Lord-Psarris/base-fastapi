from pymongo import TEXT, MongoClient
from typing import Union

import os

from .db_utils import parse_data
from .pyobjectid import PyObjectId

# setup mongo db
Client = MongoClient(os.getenv('MONGO_DB_URL'))
DB = Client.BASE_DB


class CRUDBase:
    def __init__(self, collection_name: str):
        """
        _crud-base object with default methods to Create, Read, Update, Delete (_crud-base).

        Args:
            collection_name (str): The name of the collection
        """

        self._collection = DB.get_collection(collection_name)

    @parse_data
    def get(self, *args):
        """
        This is used to get a single item based on a specific query. \n
        The first parameter is the query, the second includes the values that should be returned \n
        e.g. some_crud.get({query: "inna"}, {include_this: 1, not_this, 0})
        """
        query_parameters = list(args)
        result = self._collection.find_one(*query_parameters)

        return result

    @parse_data
    def get_by_id(self, _id: Union[str, PyObjectId]):
        """
        This is used to get a single item from the collection based on the ID passed
        """
        # ensure the id is valid
        valid_id = PyObjectId(_id)

        result = self._collection.find_one({"_id": valid_id})
        return result

    @parse_data
    def get_all(self, *args, **kwargs):
        """
        This is used to get all the items using the `find` method. \n
        The *args required are same for the `get` method. \n
        Keyword arguments include:
            `limit`: The minimum value for this is 0. And is used to limit the amount of data returned \n
            `sort`: Pass a list of tuples for mongodb to sort by \n
            `skip`: The amount of items to skip before passing the result \n
        """
        query_parameters = list(args)

        result = self._collection.find(*query_parameters, **kwargs)
        return list(result)

    @parse_data
    def get_all_using_project(self, project: dict, query=None, limit=None, sort=None):
        """
        This is used to query the db using the aggregate method, hence why the project field is needed
        :param project: The key-value map needed to move through the DB
        :param query: If the DB is being queried, pass the query here
        :param limit: same as in the `get_all` method
        :param sort: same as in the `get_all` method
        :return: cursor_list
        """

        pipeline = [{"$project": project}]

        if query is not None:
            pipeline.append({"$match": query})

        if sort is not None:
            pipeline.append({"$sort": sort})

        if limit is not None and limit > 0:
            pipeline.append({"$limit": limit})

        result = self._collection.aggregate(pipeline)
        return list(result)

    def get_all_using_list(self, items=None, field="_id", **kwargs):
        """
        This queries the database for items in the list matching the query and belonging to the field
        :param field: The field in which the items belong to. defaults to '_id'
        :param items: The list of query items belonging to the field
        :return: cursor_list
        """
        # if no items are passed return an empty list
        if items is None:
            return []

        query_list = []
        # if the field is an id field then validate them with PyObjectID
        if "_id" in field:
            for _id in items:
                # sometimes the id field comes in as a dict and should be handled
                if isinstance(_id, dict):
                    _id = _id.get("$oid", "")

                valid_id = PyObjectId(_id)
                query_list.append(valid_id)

        result = self._collection.find({field: {'$in': query_list}}, **kwargs)
        return list(result)

    @parse_data
    def get_all_using_index(self, query: Union[str, list], field=None, fields=None, project=None, sort=None, limit=0):
        """
        This is the fastest method of querying the collection for results. \n
        Note: Only collections with Text indexes can utilize this
        :param query: the data being queried. If a list is passed, set the fields' parameter
        :param field: the field in which the data is being queried
        :param fields: if the query is a list set this to a list as well
        :param project: see the 'get_all_using_project` method
        :param sort: see the 'get_all` method
        :param limit: see the 'get_all` method
        :return: cursor_list
        """

        # if a list query is passed, create a pipeline list with multiple matches, else only a single
        if isinstance(query, list):
            pipeline = []
            params = zip(query, fields)  # match each query to the respective field in the fields list

            for param in params:
                param = list(param).copy()  # we're copying as accessing directly was creating issues

                pipeline.append({"$match": {param[1]: param[0]}})

        else:
            pipeline = [
                {"$match": {"$text": {"$search": query}}},
                {"$match": {field: query}}
            ]

        if project is not None:
            pipeline.append({"$project": project})

        if sort is not None:
            pipeline.append({"$sort": sort})

        if limit is not None and limit > 0:
            pipeline.append({"$limit": limit})

        result = self._collection.aggregate(pipeline)
        return list(result)

    @parse_data
    def search_database(self, query: str, field: str, project: dict, sort=None):
        """
        This is used to search the db field using an index for the query.
        Note: a project must be passed
        :param query: The data being searched for
        :param field: The index field the data is being searched through
        :param project: see the 'get_all_using_project` method
        :param sort: see the 'get_all` method
        :return: cursor_list
        """

        pipeline = [{"$match": {field: {"$regex": query}}}, {"$project": project}]

        if sort is not None:
            pipeline.append({"$sort": sort})

        result = self._collection.aggregate(pipeline)
        return list(result)

    @parse_data
    def create(self, data: dict):
        """
        This adds new data to the collection. Ensure all the required verification to the data has been executed
        before passing the data
        :param data: The data to be added
        :return: created_item
        """
        new_item = self._collection.insert_one(data)

        # find item that has been added to verify it's been created
        created_item = self._collection.find_one({"_id": new_item.inserted_id})
        return created_item

    @parse_data
    def update(self, data: dict, item_id: Union[str, PyObjectId]):
        """
        This updated an item in the collection with the data passed
        :param data: data to update the item with
        :param item_id: id of the item in the collection
        :return: updated_item
        """
        # validate object id
        valid_id = PyObjectId(item_id)

        # remove keys with improper values
        cleaned_data = {k: v for k, v in data.items() if v is not None}

        updated_item = self._collection.update_one({"_id": valid_id}, {"$set": cleaned_data})
        return updated_item

    def delete(self, item_id: Union[str, PyObjectId]):
        """
        This deletes an item from the collection using the item_id
        :param item_id: id of the item to be deleted
        :return: 1
        """
        # validate object id
        valid_id = PyObjectId(item_id)

        self._collection.delete_one({"_id": valid_id})
        return 1

    def delete_all(self, data: list):
        """
        This deletes a list of items based on the list passed
        :param data: A list of id fields
        :return: 1
        """

        self._collection.delete_many({'_id': {'$in': data}})
        return 1

    def add_text_index(self):
        """
        this adds the text index to all the fields in the collection
        """
        self._collection.create_index([("$**", TEXT)])
