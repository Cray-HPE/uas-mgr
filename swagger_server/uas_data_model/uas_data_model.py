# MIT License
#
# (C) Copyright [2020] Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
"""Data Model Base Class for UAS Configuration
"""
from __future__ import absolute_import
from etcd3_model import Etcd3Model
from swagger_server.uas_data_model.populated_config import PopulatedConfig


class UASDataModel(Etcd3Model):
    """UAS Configuration Data Item Base Class

    This provides some common base items for any Etcd3Model in UAS and
    also manages awareness of whether a given class exists in the ETCD
    persistent data for this UAS.  If a class does not exist in ETCD,
    then the following are true:

    - A call to put() on an instance of the class will cause the
      instance to be stored (as expected) and the class to be
      registered (i.e. exist in ETCD).

    - A call to register() on the class will cause the class to be
      registered whether or not any instance is put (this allows for
      an empty table of instances of the class).

    - A call to get_all() on the class will return None instead of an
      empty list or a list of instances, indicating that the class has
      never been registered.

    - A call to other potentially problematic class methods on the
      class will be stubbed out to prevent them being called until the
      class is registered.

    If the class does exist in ETCD, then the following are true:

    - A call to put will simply cause the instance to be stored in
      ETCD as expected.

    - A call to register() will do nothing and return without failing.

    - A call to get_all() will return either an empty list (if there
      are no instances currently stored) or a list of instances (if
      there are instances stored) but never None.

    - A call to other class methods will be passed through to the
      Etcd3Model parent as presented.

    """
    # Methods for managing ETCD registration of classes
    @classmethod
    def _is_registered(cls):
        """Determine whether a given UASDataModel class is registered as a
        known class yet or not.

        """
        return PopulatedConfig.get(cls.__name__)

    @classmethod
    def register(cls):
        """Register a given UASDataModel class as a known class.

        """
        if not cls._is_registered():
            PopulatedConfig(config_name=cls.__name__).put()

    # Wrapper methods for Etcd3Model classmethods that work with
    # classes to handle registration and cases where classes are not
    # registered.
    @classmethod
    def post_event(cls, event):
        """Wrap Etcd3Model.post_event() and prevent it from being called if
        the class is not registered yet.

        """
        if cls._is_registered():
            super().post_event(event)

    @classmethod
    def get_all(cls):
        """Wrap Etcd3Model.get_all() and make it return None if
        the class is not registered yet.

        """
        if not cls._is_registered():
            return None
        return super().get_all()

    @classmethod
    def watch(cls):
        """Wrap Etcd3Model.watch() and bypass it if the class is not
        registered yet.

        """
        if cls._is_registered():
            super().watch()

    @classmethod
    def learn(cls):
        """Wrap Etcd3Model.learn() and bypass it if the class is not
        registered yet.

        """
        if cls._is_registered():
            super().learn()

    def put(self):
        """Wrap the Etcd3Model().put() method and make sure the class gets
        registered the first time I store an instance from it

        """
        if not self._is_registered():
            self.register()
        super().put()
