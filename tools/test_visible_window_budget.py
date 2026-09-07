#!/usr/bin/env python3
"""Renderer-facing aggregate geometry/draw oracle for the canonical 4x3 cue window."""
from __future__ import annotations
import json

TRIANGLES={"directional-arrow":1928,"any-note":1788,"guard":1172}
PRIMITIVES_PER_INSTANCE={"directional-arrow":3,"any-note":3,"guard":3}
# One target record per canonical 4x3 cell: eight directions, two directionless
# notes, and two guard beats. Each guard truthfully expands to two shield roots.
VISIBLE_RECORDS={"directional-arrow":8,"any-note":2,"guard":2}
INSTANCE_MULTIPLIER={"directional-arrow":1,"any-note":1,"guard":2}
MAX_VISIBLE_TRIANGLES=25000
MAX_VISIBLE_DRAW_CALLS=48
ABSOLUTE_TARGET_RECORD_CAP=12
ABSOLUTE_CUE_INSTANCE_CAP=14

def calculate():
 instances={role:VISIBLE_RECORDS[role]*INSTANCE_MULTIPLIER[role] for role in VISIBLE_RECORDS}
 triangles=sum(instances[role]*TRIANGLES[role] for role in instances)
 draw_calls=sum(instances[role]*PRIMITIVES_PER_INSTANCE[role] for role in instances)
 return instances,triangles,draw_calls

def main():
 instances,triangles,draw_calls=calculate()
 assert sum(VISIBLE_RECORDS.values())==ABSOLUTE_TARGET_RECORD_CAP
 assert sum(instances.values())==ABSOLUTE_CUE_INSTANCE_CAP
 assert triangles==23688 and triangles<=MAX_VISIBLE_TRIANGLES
 assert draw_calls==42 and draw_calls<=MAX_VISIBLE_DRAW_CALLS
 assert max(TRIANGLES.values())<4096
 print(json.dumps({"profile":"canonical-4x3-visible-window","targetRecords":VISIBLE_RECORDS,"instances":instances,"triangles":triangles,"triangleBound":MAX_VISIBLE_TRIANGLES,"drawCalls":draw_calls,"drawCallBound":MAX_VISIBLE_DRAW_CALLS},sort_keys=True))
 print("VISIBLE_WINDOW_BUDGET_OK records=12 instances=14 triangles=23688 draw_calls=42")
if __name__=="__main__": main()
