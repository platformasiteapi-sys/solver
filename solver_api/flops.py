# flops.py

"""
This file contains the classic 184 flop subset often used by PioSolver and other GTO solvers.
It mathematically represents a wide variety of board textures (monotone, wet, dry, paired, etc.)
allowing for a highly accurate estimation of overall strategy without calculating all 1755 unique flops.
"""

FLOPS_184 = [
    "AsKsQs", "AsKsJs", "AsQsJs", "AsKsTs", "AsQsTs", "AsJsTs", "AsKs9s", "AsQs9s", "AsJs9s", "AsTs9s",
    "AsKs8s", "AsQs8s", "AsJs8s", "AsTs8s", "As9s8s", "AsKs7s", "AsQs7s", "AsJs7s", "AsTs7s", "As9s7s",
    "As8s7s", "AsKs6s", "AsQs6s", "AsJs6s", "AsTs6s", "As9s6s", "As8s6s", "As7s6s", "AsKs5s", "AsQs5s",
    "AsJs5s", "AsTs5s", "As9s5s", "As8s5s", "As7s5s", "As6s5s", "AsKs4s", "AsQs4s", "AsJs4s", "AsTs4s",
    "As9s4s", "As8s4s", "As7s4s", "As6s4s", "As5s4s", "AsKs3s", "AsQs3s", "AsJs3s", "AsTs3s", "As9s3s",
    "As8s3s", "As7s3s", "As6s3s", "As5s3s", "As4s3s", "AsKs2s", "AsQs2s", "AsJs2s", "AsTs2s", "As9s2s",
    "As8s2s", "As7s2s", "As6s2s", "As5s2s", "As4s2s", "As3s2s",
    "KsQsJs", "KsQsTs", "KsJsTs", "QsJsTs",
    "KsQs9s", "KsJs9s", "KsTs9s", "QsJs9s", "QsTs9s", "JsTs9s",
    "KsQs8s", "KsJs8s", "KsTs8s", "Ks9s8s", "QsJs8s", "QsTs8s", "Qs9s8s", "JsTs8s", "Js9s8s", "Ts9s8s",
    "KsQs7s", "KsJs7s", "KsTs7s", "Ks9s7s", "Ks8s7s", "QsJs7s", "QsTs7s", "Qs9s7s", "Qs8s7s", "JsTs7s",
    "Js9s7s", "Js8s7s", "Ts9s7s", "Ts8s7s", "9s8s7s",
    "KsQs6s", "KsJs6s", "KsTs6s", "Ks9s6s", "Ks8s6s", "Ks7s6s", "QsJs6s", "QsTs6s", "Qs9s6s", "Qs8s6s",
    "Qs7s6s", "JsTs6s", "Js9s6s", "Js8s6s", "Js7s6s", "Ts9s6s", "Ts8s6s", "Ts7s6s", "9s8s6s", "9s7s6s",
    "8s7s6s",
    "KsQs5s", "KsJs5s", "KsTs5s", "Ks9s5s", "Ks8s5s", "Ks7s5s", "Ks6s5s", "QsJs5s", "QsTs5s", "Qs9s5s",
    "Qs8s5s", "Qs7s5s", "Qs6s5s", "JsTs5s", "Js9s5s", "Js8s5s", "Js7s5s", "Js6s5s", "Ts9s5s", "Ts8s5s",
    "Ts7s5s", "Ts6s5s", "9s8s5s", "9s7s5s", "9s6s5s", "8s7s5s", "8s6s5s", "7s6s5s",
    "KsQs4s", "KsJs4s", "KsTs4s", "Ks9s4s", "Ks8s4s", "Ks7s4s", "Ks6s4s", "Ks5s4s", "QsJs4s", "QsTs4s",
    "Qs9s4s", "Qs8s4s", "Qs7s4s", "Qs6s4s", "Qs5s4s", "JsTs4s", "Js9s4s", "Js8s4s", "Js7s4s", "Js6s4s",
    "Js5s4s", "Ts9s4s", "Ts8s4s", "Ts7s4s", "Ts6s4s", "Ts5s4s", "9s8s4s", "9s7s4s", "9s6s4s", "9s5s4s",
    "8s7s4s"
]

# NOTE: The above is just a truncated illustrative array for monotonic flops.
# In the actual script, we will load the standard 184 subset text file.
