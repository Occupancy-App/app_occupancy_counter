import tornado.web
import uuid
import time
import datetime
import logging
import redis
import json
from . import occupancy_api_utils


class NewSpaceHandler(tornado.web.RequestHandler):

    # Note -- should not override __init__, per 
    #       https://www.tornadoweb.org/en/stable/web.html#tornado.web.RequestHandler
    def initialize(self):
        self._db_handle = redis.Redis( host='redis' )


    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin",      "*")
        self.set_header("Access-Control-Allow-Headers",     "x-requested-with")
        self.set_header('Access-Control-Allow-Methods',     "PUT, OPTIONS")

 
    def options(self, current_occupancy, max_occupancy, name_group, space_name ):
        self.set_status(204)
        self.finish()


    def put( self, current_occupancy, max_occupancy, name_group, space_name ):
        current_occupancy = int( current_occupancy ) 
        max_occupancy = int( max_occupancy ) 

        # Sanity check occupancy
        if max_occupancy < 1 or max_occupancy > 100000:
            self.set_status( 400, 
                "Invalid occupancy value: {0}, passed value must be 1 <= max_occupancy <= 100000".format(
                    max_occupancy) )
            self.finish()
        else:
            if current_occupancy < 0:
                current_occupancy = 0

            new_space_id = uuid.uuid4()

            now_timestamp = "{0}Z".format(datetime.datetime.utcnow().isoformat())

            ttl_seconds = occupancy_api_utils.key_expire_value

            expiration_seconds_since_epoch = time.time() + ttl_seconds

            # If persisting the output works, send it back to the client in *API* format
            api_output = occupancy_api_utils.write_new_space_to_db( self._db_handle, 
                    new_space_id, space_name, int(current_occupancy), int(max_occupancy) )

            self.write( api_output )

 
    def _write_space_to_db( self, space_id, space_info ):
        try:
            # can't write a raw UUID object, cast to a string
            space_redis_key = str( space_id )

            self._db_handle.set( space_redis_key, json.dumps(space_info) ) 
            logging.debug("Successful write of JSON for space {0}".format(space_id) )
            return True
        except redis.RedisError as e:
            logging.warn("Exception thrown writing JSON for space {0}: {1}".format(space_id, e) )
            return False
