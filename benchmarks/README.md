# Benchmarks

Benchmarks would be built in this directory. You can build all 15 programs we used in paper with [make-benchmark.sh](make-benchmark.sh). You can get the list of available benchmarks with following command:
```bash
$ ./make-benchmark.sh --list
```
If you want to build all 15 benchmarks, you can use following command:
```bash
$ ./make-benchmark.sh all
```
Also, you can build multiple objects for parallel execution. By default, if you use a [Dockerfile](/Dockerfile), only one object will be built. If you want to enable parallel execution, you should build additional objects using the following command.
```bash
$ ./make-benchmark.sh --n-objs {N you want} {program}
```
