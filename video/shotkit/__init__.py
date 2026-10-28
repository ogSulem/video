"""Small, dependency-light toolkit for building continuous shots from keyframes.

The shot renderer composes a single continuous camera take out of a chain of
approved keyframes: dense optical-flow warping between neighbours, a smooth
camera move (push-in + drift) driven by a C1-continuous timeline, procedural
atmospheric snow, a physically-motivated powder burst, and a film-grade
finishing pass (shutter blur, grain, vignette).
"""
