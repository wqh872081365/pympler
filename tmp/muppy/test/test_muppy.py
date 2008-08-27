import doctest
import random 
import unittest

import muppy
import muppy.muppy

# default to asizeof if sys.getsizeof is not available (prior to Python 2.6)
try:
    from sys import getsizeof as _getsizeof
except ImportError:
    from utils import asizeof
    _getsizeof = asizeof.flatsize
    
class MuppyTest(unittest.TestCase):

    def test_objects(self):
        """Check that objects returns a non-empty list."""
        self.failUnless(len(muppy.get_objects()) > 0)

    def test_diff(self):
        """Check if the diff of to object lists is correct.

        The diff has to work in both directions, that is it has to show
        newly created objects, as well as removed objects.
        The sorting is irrelevant.
        """
        (o1, o2, o3, o4, o5, o6) = (1, 'a', 'b', 4, 5, (1,))
        list1 = [o1, o2, o3, o4]
        list2 = [o1, o2, o3, o4, o5]
        list3 = [o5, o3, o1, o4, o2]
        list4 = [o1, o2, o3, o4, o6]

        # empty lists
        expected = {'+': [], '-': []}
        self.assertEqual(muppy.get_diff([], []), expected)
        # one more entry
        expected = {'+': [o5], '-': []}
        self.assertEqual(muppy.get_diff(list1, list2), expected)
        # one more entry, but different order
        self.assertEqual(muppy.get_diff(list1, list3), expected)
        # one entry removed
        expected = {'+': [], '-': [5]}
        self.assertEqual(muppy.get_diff(list2, list1), expected)
        # one entry removed, but different order
        self.assertEqual(muppy.get_diff(list3, list1), expected)
        # one more entry of different type
        expected = {'+': [o6], '-': []}
        self.assertEqual(muppy.get_diff(list1, list4), expected)

    def test_filter_by_type(self):
        """Check that only elements of a certain type are included,
        no elements are removed which belong to this type and 
        no elements are added."""
        s = (s1, s2, s3, s4) = ('', 'a', 'b', 'a')
        t = (t1, t2) = (dict, str)
        i1 = 1
        l1 = 1L
        objects = [s1, s2, i1, l1, t1, t2, s3, s4]
        
        objects = muppy.filter(objects, Type=str)
        self.assertEqual(len(objects), len(s))
        for element in s:
            self.assertEqual(element in objects, True)

    def test_filter_by_size(self):
        """Check that only elements within the specified size boundaries 
        are returned. 
        Also verify that if minimum is larger than maximum an exception is 
        raised."""
        minimum = 42
        maximum = 958
        objects = []
        for i in range(1000):
            rand = random.randint(0,1000)
            objects.append(' ' * rand)
        objects = muppy.filter(objects, min=minimum, max=maximum)
        for o in objects:
            self.assert_(minimum <= _getsizeof(o) <= maximum)

        self.assertRaises(ValueError, muppy.filter, objects, min=17, max=16)

    def test_get_referents(self):
        """Check that referents are included in return value.

        Per default, only first level referents should be returned.
        If specified otherwise referents from even more levels are included
        in the result set.

        Duplicates have to be removed."""
        (o1, o2, o3, o4, o5) = (1, 'a', 'b', 4, 5)
        l0 = [o1, o2]
        l1 = [10, 11, 12, 13, l0]
        l2 = [o1, o2, o3, o4, o5, l1]

        #return all objects from first level
        res = muppy.get_referents(l2, level=1)
        self.assertEqual(len(l2), len(res))
        for o in res:
            self.assert_(o in l2)

        # return all objects from first and second level
        res = muppy.get_referents(l2, level=2)
        self.assertEqual(len(l1) + len(l2), len(res))
        for o in res:
            self.assert_((o in l1) or (o in l2))

        # return all objects from all levels, but with duplicates removed
        res = muppy.get_referents(l2, level=4242)
        self.assertEqual(len(l1) + len(l2), len(res))
        for o in res:
            self.assert_((o in l0) or (o in l1) or (o in l2))
        
    def test_get_size(self):
        """Check that the return value is the sum of the size of all objects."""
        (o1, o2, o3, o4, o5) = (1, 'a', 'b', 4, 5)
        list = [o1, o2, o3, o4, o5]
        expected = 0
        for o in list:
            expected += _getsizeof(o)

        self.assertEqual(muppy.get_size(list), expected)

        # do to the poor performance excluded from tests, for now
#    def test_get_usage(self):
#        """Check that the return value reflects changes to the memory usage.
#
#        For functions which leave the memory unchanged a None should be
#        returned.
#
#        Parameters of the function should be forwarded correctly.
#        """
#        
#        # we need to pull some tricks here, since parsing the code, static
#        # objects are already created, e.g. parsing "a = 'some text'" will
#        # already create a string object for 'some text'. So we compute the
#        # values to use dynamically.
#        
#        # check that no increase in memory usage returns None
#        a = 1
#        b = 2
#        c = 3
#        d = 4
#        e = 1
#        def function(): pass
#        expected = None
#        # XXX: Fix get_usage tests.
#        res = muppy._get_usage(function)
#        print res
#        self.assertEqual(res, expected)
#        # passing of parameter should also work
#        def function(arg):
#            a = arg
#        expected = None
#        res = muppy._get_usage(function, 42)
#        self.assertEqual(res, expected)
#        # memory leaks should be indicated
#        def function():
#            try:
#                muppy.extra_var.append(1)
#            except AttributeError:
#                muppy.extra_var = []
#        res = muppy._get_usage(function)
#        self.assert_(res is not None)

    def test_is_containerobject(self):
        """Check that (non-)container objects are identified correctly."""
        self.assertTrue(muppy.muppy._is_containerobject([]))
        self.assertTrue(muppy.muppy._is_containerobject((1,)))
        self.assertTrue(muppy.muppy._is_containerobject({}))
        self.assertTrue(muppy.muppy._is_containerobject(int))
        self.assertTrue(muppy.muppy._is_containerobject(type))

        self.assertFalse(muppy.muppy._is_containerobject(1))
        self.assertFalse(muppy.muppy._is_containerobject(''))
        
    def test_remove_duplicates(self):
        """Verify that this operations returns a duplicate-free lists. 
        
        That, is no objects are listed twice. This does not apply to objects
        with same values."""
        (o1, o2, o3, o4, o5) = (1, 'a', 'b', 'a', 5)
        objects = [o1, o2, o3, o4, o5, o5, o4, o3, o2, o1]
        expected = set(objects)
        res = muppy.muppy._remove_duplicates(objects)
        self.assertEqual(len(expected), len(res))
        for o in res:
            self.assert_(o in expected)

    def test_sort(self):
        """Check that objects are sorted by size."""
        objects = ['', 'a', 'ab', 'ab', 'abc', '0']
        objects = muppy.sort(objects)
        while len(objects) > 1:
            prev_o = objects.pop(0)
            self.assert_(_getsizeof(objects[0]) >= _getsizeof(prev_o),\
                 "The previous element appears to be larger than the " +\
                 "current: %s<%s" % (prev_o, objects[0]))

        
            
def suite():
    suite = unittest.makeSuite(MuppyTest,'test') 
    suite.addTest(doctest.DocTestSuite())
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
