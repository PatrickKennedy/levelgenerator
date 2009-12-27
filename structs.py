#!/usr/bin/env python
import logging

from collections import namedtuple

Point = namedtuple('Point', 'x y')
Point.__add__ = lambda x, y: Point(x.x + y.x, x.y + y.y) if isinstance(y, Point) else Point(x.x + y, x.y + y)
Point.__sub__ = lambda x, y: Point(x.x - y.x, x.y - y.y) if isinstance(y, Point) else Point(x.x - y, x.y - y)
Point.__mul__ = lambda x, y: Point(x.x * y.x, x.y * y.y) if isinstance(y, Point) else Point(x.x * y, x.y * y)
Point.__div__ = lambda x, y: Point(x.x / y.x, x.y / y.y) if isinstance(y, Point) else Point(x.x / y, x.y / y)
Point.__ge__ = lambda x, y: x.x >= y.x and x.y >= y.y
Point.__gt__ = lambda x, y: x.x > y.x and x.y > y.y
Point.__le__ = lambda x, y: x.x <= y.x and x.y <= y.y
Point.__lt__ = lambda x, y: x.x < y.x and x.y < y.y
Point.floor = lambda self: Point(int(self.x), int(self.y))

class Rect(object):
	def __init__(self, left, top, width, height, absolute=False):
		self.left = left
		self.top = top
		if absolute:
			self.width = width-left
			self.height = height-top
		else:
			self.width = width
			self.height = height

	def __repr__(self):
		return "Rect(%s, %s, %s, %s)" % (self.left, self.top, self.right, self.bottom)

	def __contains__(self, other):
		if isinstance(other, Point):
			return self.left < other.x < self.right \
				and self.top < other.y < self.bottom
		return self.right	> other.left \
			and self.left	< other.right \
			and self.bottom	> other.top \
			and self.top	< other.bottom

	def __gt__(self, other):
		return self.left	< other.left \
			and self.top	< other.top \
			and self.right	> other.right \
			and self.bottom	> other.bottom

	def __ge__(self, other):
		return self.left	<= other.left \
			and self.top	<= other.top \
			and self.right	>= other.right \
			and self.bottom	>= other.bottom

	def __eq__(self, other):
		return self.left	== other.left \
			and self.top	== other.top \
			and self.right	== other.right \
			and self.bottom	== other.bottom

	def __lt__(self, other):
		return self.left	> other.left \
			and self.top	> other.top \
			and self.right	< other.right \
			and self.bottom	< other.bottom

	def __le__(self, other):
		return self.left	>= other.left \
			and self.top	>= other.top \
			and self.right	<= other.right \
			and self.bottom	<= other.bottom

	def __add__(self, other):
		return Rect(self.left+other.left, self.top+other.top,
					self.right+other.right, self.bottom+other.bottom)

	def __sub__(self, other):
		return Rect(self.left-other.left, self.top-other.top,
					self.right-other.right, self.bottom-other.bottom)

	def __iter__(self):
		return (x for x in [self.left, self.top, self.right, self.bottom])
		return [(self.left, self.top), (self.right, self.bottom)]

	def pos_in(self, rect):
		"""Return this Rect's position in the passed Rect."""
		matched = []
		if isinstance(rect, Rect):
			cx, cy = rect.center
		else:
			cx, cy = rect
		# The >= for the right and bottom is required because the center
		# point actually corresponds to a rectangle, so it's off center.
		if self.left < cx and self.top < cy: matched.append(0)
		if self.right > cx and self.top < cy: matched.append(1)
		if self.right > cx and self.bottom > cy: matched.append(2)
		if self.left < cx and self.bottom > cy: matched.append(3)
		return matched

	def copy(self):
		return Rect(self.left, self.top, self.width, self.height)

	def fracture(self, point):
		"""Fracture self about point and return the results

		Rects that aren't fractured are filled with None

		"""
		logging.debug("Fracturing %s about %s" % (self, point))
		# We assume the point is the origin of another rect.
		shards = [None, None, None, None]
		# Brute forcing shards until I have time to rewrite the other code
		# (ironically this is probably faster than the other code would be)
		poses = self.pos_in(point)
		px, py = point
		if 0 in poses:
			shards[0] = Rect(self.left, self.top,
							 min(self.right, px),
							 min(self.bottom, py),
							 absolute=True)
		if 1 in poses:
			shards[1] = Rect(max(self.left, px),
							 self.top, self.right,
							 min(self.bottom, py),
							 absolute=True)
		if 2 in poses:
			shards[2] = Rect(max(self.left, px),
							 max(self.top, py),
							 self.right, self.bottom,
							 absolute=True)
		if 3 in poses:
			shards[3] = Rect(self.left,
							 max(self.top, py),
							 min(self.right, px),
							 self.bottom,
							 absolute=True)
		#print "Resulting Shards", shards
		return shards


	def get_bottom(self): return self.top+self.height
	def set_bottom(self, v): self.height = v-self.top
	bottom = property(get_bottom, set_bottom)

	def get_right(self): return self.left+self.width
	def set_right(self, v): self.width = v-self.left
	right = property(get_right, set_right)


	@property
	def center(self): return Point(self.left+(self.width/2), self.top+(self.height/2))
	@property
	def ul(self): return Point(self.left, self.top)
	@property
	def lr(self): return Point(self.right, self.bottom)
