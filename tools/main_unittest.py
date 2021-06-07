import math
import unittest

import init
import lib.util
import lib.labeler


class TestLine(unittest.TestCase):

    def test_line(self):
        x1, y1, x2, y2, a, b = range(6)

        # check: create_from_points
        line = lib.labeler.Line.create_from_points(x1, y1, x2, y2)
        self.assertEqual(line.get_x(y1), x1)
        self.assertEqual(line.get_y(x1), y1)
        self.assertEqual(line.get_x(y2), x2)
        self.assertEqual(line.get_y(x2), y2)

        # check: create_from_pointl
        line = lib.labeler.Line.create_from_pointk(x1, y1, a, b)
        other = lib.labeler.Line.create_from_pointk(0, 0, a, b)
        self.assertTrue(line.parallel_to(other))

        # check: create_from_pointa
        angle = line.get_slant_angle()
        other = lib.labeler.Line.create_from_pointa(x2, y2, angle)
        self.assertTrue(line.parallel_to(other))

        # check: get_cross_point. get_distance
        line1 = lib.labeler.Line.create_from_points(0, 0, 1, 1)
        line2 = lib.labeler.Line.create_from_points(1, 0, 0, 1)
        cross = line1.get_cross_point(line2)
        distance = line2.get_distance(0, 0)
        self.assertEqual(cross, (0.5, 0.5))
        self.assertAlmostEqual(distance, 0.5 * math.sqrt(2))

        # check: move_to_point
        line = lib.labeler.Line.create_from_pointk(x1, y1, a, b)
        other = lib.labeler.Line.create_from_pointk(x1, y1, a, b)
        other.move_to_point(x2, y2)
        self.assertAlmostEqual(other.get_y(x2), y2)
        self.assertTrue(other.parallel_to(line))

        # check: left_to, right_to, above_to, below_to
        line = lib.labeler.Line.create_from_points(x1, y1, x2, y2)
        self.assertTrue(line.left_to(x1 + 1, y1))
        self.assertTrue(line.right_to(x1 - 1, y1))
        self.assertTrue(line.above_to(x1, y1 - 1))
        self.assertTrue(line.below_to(x1, y1 + 1))


if __name__ == '__main__':
    unittest.main()