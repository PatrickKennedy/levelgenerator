#!/usr/bin/env python

import blocks
from structs import Rect

def test_valid_single_room():
	tree = blocks.Quad(Rect(0, 0, 32, 32))

	room = blocks.Room(Rect(3, 3, 16, 7), name='cool_room')
	tree.charge(room)
	hits = tree.hit(Rect(3, 4, 5, 6))
	assert hits == set([room])

def test_invalid_single_room():
	tree = blocks.Quad(Rect(0, 0, 32, 32))

	room = blocks.Room(Rect(3, 3, 16, 7), name='cool_room')
	tree.charge(room)
	hits = tree.hit(Rect(0, 0, 1, 2))
	assert set([room]) not in hits

def test_valid_two_room():
	tree = blocks.Quad(Rect(0, 0, 32, 32))

	room = blocks.Room(Rect(3, 3, 16, 7), name='cool_room')
	tree.charge(room)

	bed = blocks.Bed(Rect(0, 0, 5, 8), room, name='cool_bed')
	tree.charge(bed)

	hits = tree.hit(bed.pillow.rect)#tree.hit(Rect(3, 4, 2, 2))
	assert hits == set([room, bed, bed.pillow])

def test_removal():
	tree = blocks.Quad(Rect(0, 0, 32, 32))

	room = blocks.Room(Rect(3, 3, 16, 7), name='cool_room')
	tree.charge(room)

	bed = blocks.Bed(Rect(0, 0, 5, 8), room, name='cool_bed')
	tree.charge(bed)

	bed.tear_down()

	hits = tree.hit(bed.pillow.rect)#tree.hit(Rect(3, 4, 2, 2))
	assert set([bed, bed.pillow]) not in hits
