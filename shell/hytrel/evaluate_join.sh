python scripts/hytrel/evaluate_benchmark_join.py wiki-join-jaccard --K 10 --scale 1.0 --benchmark_file data/wiki-join-jaccard/benchmark.pkl --metrics_file hytrel_no_rerank.json
python scripts/hytrel/evaluate_benchmark_join.py wiki-join-jaccard --K 10 --scale 1.0 --rerank --rerank_factor 3 --threshold 0.05 --num_perm 256 --benchmark_file data/wiki-join-jaccard/benchmark.pkl --metrics_file hytrel_with_rerank_rf3_th_05.json
python scripts/hytrel/evaluate_benchmark_join.py wiki-join-jaccard --K 10 --scale 1.0 --rerank  --rerank_factor 10 --threshold 0.05 --num_perm 256 --benchmark_file data/wiki-join-jaccard/benchmark.pkl --metrics_file hytrel_with_rerank_rf10_th_05.json