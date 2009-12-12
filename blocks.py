#!/usr/bin/env python
import logging
import random
import sys

import Image, ImageColor, ImageDraw

LEVELS = {
	'debug':logging.DEBUG,
	'info':logging.INFO,
	'warning':logging.WARNING,
	'error':logging.ERROR,
	'critical':logging.CRITICAL,
}

FORMAT = "%(levelname)-6s %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)

from structs import Rect

def get_bounding_box(quads):
	l = min(quad.rect.left for quad in quads)
	t = min(quad.rect.top for quad in quads)
	r = max(quad.rect.right for quad in quads)
	b = max(quad.rect.bottom for quad in quads)
	return Rect(l, t, r-l, b-t)

class Quad(object):
	"""A meta-block that contains the overall structure of the tree."""
	def __init__(self, rect, parent=None):
		self.rect = rect
		self.parent = parent
		# Empty (None) quads propigate data from the first sibling
		self.quads = [None, None, None, None]
		self.charges = set([])
	
	def __repr__(self):
		return "Quad(%s)" % (self.rect,)
		
	def tear_down(self):
		#print "--- Tearing down %s" % self
		self.parent.quads[self.parent.quads.index(self)] = None
		del self

	@property
	def root(self):
		"""Recursively walk up the tree to the root"""
		return self.parent.root if self.parent else self

	def hit(self, rect, strict=False):
		"""Return a set of blocks that collide with a passed rect.
		
		If strict is True then only blocks whose rects are fully contained
		in the passed rect are returned.
		
		"""
		if self.rect in rect:
			if strict:
				hits = set(block for block in self.charges if block.rect <= self.rect)
			else:
				hits = set(block for block in self.charges if block.rect in self.rect)
			poses = rect.pos_in(self.rect)
			for pos in poses:
				quad = self.quads[pos]
				if quad is None:
					continue
				hits |= quad.hit(rect, strict)
				
			return hits
		else:
			return self.parent.hit(rect, strict)

	def charge(self, block):
		"""Charge a block to the Quad's care"""
		logging.info("--- %s %s" % (block.name, '-' * (79-5-7-len(block.name))))
		logging.info("Charging %s to %s" % (block, self))
		if False and block.parent:
			logging.info("Beginning from %s" % block.parent.quads[0])
			#print "%s Parent ==" % block, block.parent, block.parent.quads
			#quads = block.parent.quads[0]._allocate(block.rect)
		else:
			quads = self._allocate(block.rect, block.exclude)
		#quads.sort()
		block.quads = quads
		logging.info("Finished charging %s" % block)
		[quad.charges.add(block) for quad in quads]
		
		for child in block.children:
			self.charge(child)

	def dismiss(self, block, rect=None):
		"""Dismiss a block, or a rect portion of one, from a quad's service"""
		block.tear_down(rect)
			
	def _assign_new_quads(self, shards):
		"""Create any quads we'll need all at once. At most one fracture call."""
		# Positions of quads we need to allocate our rect which we don't have
		needed = [x for x in range(len(shards)) if shards[x] and not self.quads[x]]
		if needed:
			new_quads = self.rect.fracture(self.rect.center)
			for pos in needed:
				self.quads[pos] = Quad(new_quads[pos], self)
				logging.debug("Generating new %s" % self.quads[pos])

	def _allocate(self, rect, exclude=None, matched=None):
		"""Return a list of quads allocated for the given rect."""
		if matched is None:
			matched = []
		
		if exclude and rect in exclude:
			return matched
		
		# Append ourself if we are a matching quad.
		elif self.rect == rect:
			#print "A match! %s == %s" % (self.rect, rect)
			matched.append(self)
			
		# If the passed rect is smaller than and fully contained within this one
		elif rect <= self.rect:
			logging.debug("Subdividing %s" % rect)
			shards = rect.fracture(self.rect.center)
			self._assign_new_quads(shards)
			#print shards, rect.pos_in(self.rect)
			for pos, r in enumerate(shards):
				if not r:
					continue
				self.quads[pos]._allocate(r, exclude, matched)
			
		# If the given rect contains this rect
		elif self.rect <= rect:
			logging.debug("Stepping Up to %s" % self.parent)
			self.parent._allocate(rect, exclude, matched)

		# If the rect extends outside this quad then we need to 
		# split it across multiple Quads
		elif rect not in self.rect and self.parent:
			logging.debug("Rooting... %s | %s" % (rect, self.rect))
			self.root._allocate(rect, exclude, matched)
					
		return matched

class Block(object):
	"""Base building block"""
	layer = 1
	
	def __init__(self, rect, parent=None, name='', abs=False, exclude=None, **kwargs):
		self.name = name or self.__class__.__name__.lower()
		self._rect = rect
		self._exclude = exclude or Rect(-1, -1, 0, 0)
		self.abs = abs
		self.parent = parent
		if parent:
			self.parent.children.add(self)
		self.quads = []
		self.children = set([])
		self.init(**kwargs)
		
	def init(*args, **kwargs):
		"""Intended to be overwritten by subclasses."""
		pass
	
	def __repr__(self):
		return "%s(name: %s, %s, quads: %s)" % (
			self.__class__.__name__,
			self.name,
			self.rect,
			len(self.quads)
		)
	
	def tear_down(self, rect=None):
		"""Tear down the block, performing related clean up.
		
		If a Rect is passed then just that portion of the Block will be acted on.
		
		"""
		logging.info("-- Tearing down %s" % self)
		for quad in set(self.quads):
			if rect is None or (rect and quad.rect in rect):
				self.quads.remove(quad)
				quad.charges.remove(self)
				if not quad.charges:
					quad.tear_down()
			
		if not self.quads and self.parent:
			self.parent.children.discard(self)
			
	def get_rect(self):
		if not self.abs and self.parent:
			#TODO: Optimize this calculation
			return Rect(self.parent.rect.left+self._rect.left,
						self.parent.rect.top+self._rect.top,
						self._rect.width, self._rect.height)
		else:
			return self._rect
		
	def set_rect(self, rect):
		self._rect = rect
		
	rect = property(get_rect, set_rect)
		
	def get_exclude(self):
		if not self.abs and self.parent:
			#TODO: Optimize this calculation
			return Rect(self.parent.rect.left+self._exclude.left,
						self.parent.rect.top+self._exclude.top,
						self._exclude.width, self._exclude.height)
		else:
			return self._exclude
		
	def set_exclude(self, rect):
		self._exclude = rect
		
	exclude = property(get_exclude, set_exclude)
	
	def type_root(self):
		return self.parent is None or not isinstance(self.parent, self.__class__)

class Level(Block):
	"""A container for all the Blocks in a level"""
	
class Room(Block):
	"""An arbitrary room."""
	def init(self, wall_class=None):
		if wall_class is None:
			wall_class = Wall
		self.wall = wall_class(self.rect, self)
		self.wall.color = ImageColor.getrgb('chocolate')
	
class Wall(Block):
	"""An arbitrary wall."""
	MATERIAL = {'wood':0, 'stone':1}
	TYPE = {'invisible':-1, 'solid':0, 'fence':1}
	layer = 2
		
	def __init__(self, rect, parent=None, name='', abs=False, exclude=None,
				 thickness=1, **kwargs):
		rect = Rect(-thickness, -thickness,
					rect.width+2*thickness,
					rect.height+2*thickness)
		super(Wall, self).__init__(rect, parent, name, abs, exclude,
								   thickness=thickness, **kwargs)
		
	def init(self, thickness=1, type='solid', material='wood'):
		#self.rect = Rect(-thickness, -thickness,
		#				 self.rect.width+2*thickness,
		#				 self.rect.height+2*thickness)
		self.thickness = thickness
		self.type = type
		self.material = material
	
class Window(Block):
	"""An arbitrary window."""
	TYPE = {'clear':0, 'stained':1}
	
	
class Furniture(Block):
	"""An arbitrary piece of furniture."""
	
class Decor(Block):
	"""An arbitrary decor item."""
	
class Object(Block):
	"""An arbitrary object."""
	
class Bedroom(Room):
	def init(self, wall_class=None):
		if rect.width < 5 and rect.height < 5:
			rect.width = random.randint(5, 8)
			rect.height = random.randint(5, 8)
		super(Bedroom, self).init(wall_class)
	
class Bed(Furniture):
	def init(self, color=ImageColor.getrgb('white'),
			 decor_color=ImageColor.getrgb('blue')):
		self.color = color
		
		self.pillow = Decor(Rect(1, 1, 2, 1), self, 'pillow')
		self.pillow.color = decor_color
		
		self.sheet = Decor(Rect(0, 3, 4, 5), self, 'sheet')
		self.sheet.color = decor_color
		
	def tear_down(self):
		self.pillow.tear_down()
		self.sheet.tear_down()
		super(Bed, self).tear_down()
	
if __name__ == "__main__":
	if len(sys.argv) > 1:
		level_name = sys.argv[1]
		level = LEVELS.get(level_name, logging.NOTSET)
		logging.root.setLevel(level)
	
	mode = 'RGB'
	size = 32
	scale = 1
	def build_tree():
		tree = Quad(Rect(0, 0, size, size))
		level = Level(Rect(0, 0, size, size))
		level.color = ImageColor.getcolor('grey', mode)
		tree.charge(level)
		
		room = Room(Rect(4, 4, 16, 16), level, name='room')
		room.color = ImageColor.getcolor('orange', mode)
		tree.charge(room)
		
		table = Furniture(Rect(0, 0, 4, 3), room, name='table')
		table.color = ImageColor.getcolor('brown', mode)
		
		lamp = Furniture(Rect(1, 1, 1, 1), table, name='lamp')
		lamp.color = ImageColor.getcolor('yellow', mode)
		
		tree.charge(table)
		
		bed = Bed(Rect(4, 0, 4, 8), room, color=ImageColor.getrgb('white'),
				 decor_color=ImageColor.getrgb('darkcyan'))
		tree.charge(bed)
		
		bed2 = Bed(Rect(9, 0, 4, 8), room, color=ImageColor.getrgb('white'),
				 decor_color=ImageColor.getrgb('crimson'))
		tree.charge(bed2)
		
		bed2.tear_down()
		
		#bed = Furniture(Rect(4, 0, 4, 8), room, name='bed')
		#bed.color = ImageColor.getcolor('green', mode)
		#tree.charge(bed)
		
		#pillow = Furniture(Rect(1, 1, 2, 1), bed, name='pillow')
		#pillow.color = ImageColor.getcolor('white', mode)
		#tree.charge(pillow)
		
		#sheet = Furniture(Rect(0, 3, 4, 5), bed, name='sheet')
		#sheet.color = ImageColor.getcolor('white', mode)
		#tree.charge(sheet)
		
		lump = Block(Rect(32, 32, 8, 8), room, name='lump', abs=True)
		lump.color = ImageColor.getcolor('black', mode)
		tree.charge(lump)
		
		return tree
		
	def draw_tree(tree, canvas):
		charges = list(tree.charges)
		# Force lower layers to the front of the line
		charges.sort(key=lambda x: x.layer)
		for block in charges:
			logging.info("Painting: %s\t%s" % (block.name, tree.rect))
			box = list(tree.rect)
			box[2] -= 1
			box[3] -= 1
			canvas.rectangle(box, fill=block.color)
		for quad in tree.quads:
			if quad:
				draw_tree(quad, canvas)	

	def test():
		scaled = size*scale
			
		im = Image.new(
			mode, (scaled, scaled),
			color=ImageColor.getcolor('rgb(124, 124, 124)', mode)
		)
		canvas = ImageDraw.Draw(im)
		
		tree = build_tree()
		draw_tree(tree, canvas)
		
		#box = [Point(size/6, size/6) * scale, (Point(size-size/6, size-size/6) * scale)-1]
		#canvas.rectangle(box, fill=colors[random.randint(0, 1)])
		im = im.resize((size*10, size*10))
		name = 'level.png'
		logging.info("Saving to %s" % name)
		im.save(name)

	test()
	
	
	