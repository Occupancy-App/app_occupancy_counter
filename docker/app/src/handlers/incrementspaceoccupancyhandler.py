import tornado.web
import uuid
import time
import datetime
import logging
import redis
import json
import sys
from . import occupancy_api_utils 


class IncrementSpaceOccupancyHandler(tornado.web.RequestHandler):

    # Note -- should not override __init__, per 
    #       https://www.tornadoweb.org/en/stable/web.html#tornado.web.RequestHandler
    def initialize(self):
        self._db_handle = redis.Redis( host='redis' )


    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin",      "*")
        self.set_header("Access-Control-Allow-Headers",     "x-requested-with")
        self.set_header('Access-Control-Allow-Methods',     "PUT, OPTIONS")

 
    def options( self, space_id ):
        self.set_status(204)
        self.finish()


    def put( self, space_id ):
        try:
             # Make sure the space ID string is a legit UUID
            space_uuid = uuid.UUID( "urn:uuid:{0}".format(space_id) )
        except:
            logging.warn("Space ID not a GUID in {0}".format(space_id) )
            self.set_status( 400 )
            self.write( { "error": "Submitted ID {0} is not a valid GUID".format(space_id) } )
            self.finish()
            return

        # Attempt the increment
        try:
            logging.debug("About to try increment for {0}".format(str(space_uuid)) )
            increment_response = occupancy_api_utils.increment_occupancy(self._db_handle, space_uuid)

            # None means no space with that ID was found, otherwise we get a valid dictionary to write back out
            if increment_response is None:
                self.set_status( 404, "Space ID {0} was not found".format(space_id) )
                self.write( { "error": "Space ID {0} was not found".format(space_id) } )
            else:
                self.write( increment_response )

        except redis.RedisError as e:
            self.set_status( 500, "Redis error: {0}".format(e) )
            self.finish()
            return
        except:
            e = sys.exc_info()[0]
            logging.warn("Unhandled exception thrown in increment operation: {0}".format(e))
            self.set_status( 500, "Unhandled exception in increment" )
            self.finish()
            return
