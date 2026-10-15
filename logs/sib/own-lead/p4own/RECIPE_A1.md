Provenance: Project HERCULES | owner the owner | [id removed]

# RECIPE-A1: implementation fix to train.py (no recipe change). Pushed before any training step has completed or any map exists.
- Fault: train.load_data concatenated the memory-mapped shards (np.concatenate), which materialised the 17 GB in RAM.
  - The first S1 launch (13:05Z) was OOM-killed during data loading (dmesg: Memory cgroup out of memory, pid 5708, anon-rss 13.9 GB).
  - It had run 0 training steps.
- Fix: a lazy ShardCat that indexes the mmapped shards. Item i equals np.concatenate(parts)[i] (unit test). Every other line of train.py is unchanged.
  - Batches, schedule, loss, optimiser, seeds and all RECIPE.md parameters are identical.
- train.py sha256: 2943cac435c2a9b425eae794708bf18dbec2abc033da5a2fd283fc991052a0f3 (RECIPE.md) -> 9a8ad9b2e83191fb42cb423db4b0e4e35cd213921ba1578db760d5b879c31c56.
- test_own.py gains the ShardCat equality test; tests ALL OK.
- Arm workers use train.py (and test_own.py) from this commit; all other code stays at 6b5bdc5.
