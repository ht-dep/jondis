import logging

import redis

from jondis.pool import Pool
from jondis.tests.base import BaseJondisTest

logger = logging.getLogger(__name__)


class SlavePromotionTest(BaseJondisTest):

    def start(self):
        self.master = self.manager.start('master')
        self.slave = self.manager.start('slave', self.master)

        assert self.master > 0
        assert self.slave > 0

    def test_promotion_on_failure(self):
        pool = Pool(hosts=['127.0.0.1:{0}'.format(self.master)])
        r = redis.StrictRedis(connection_pool=pool)

        r.set('test', 1)
        r.get('test2')

        self.manager.stop('master')

        redis.StrictRedis('localhost', self.slave)

        # promote slave to master
        self.manager.promote(self.slave)
        self.master = self.slave

        with self.assertRaises(redis.ConnectionError):
            r.get('test2')

        r.get('test2')
        self.pool = pool
        self.r = r

    def test_multiple_cascading_failures(self):
        self.test_promotion_on_failure()

        self.slave = self.manager.start('slave2', self.master)
        self.pool._configure()

        self.manager.stop('slave')
        self.manager.promote(self.slave)

        logger.debug("Force reconfigure")

        r = self.r
        with self.assertRaises(redis.ConnectionError):
            r.get('test2')

        r.get('test2')
