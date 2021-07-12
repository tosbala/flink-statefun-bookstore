# flink-statefun-bookstore

Sample book store application using flink stateful functions' `Python SDK`.
Demonstrates some of the core capabilities of flink statefun.
Taken inspirations from [Statefun Playground](https://github.com/apache/flink-statefun-playground) and [Statefun Workshop](https://github.com/ververica/flink-statefun-workshop)


## Running the example

```
docker-compose build
docker-compose up
```

Sample producer makes random orders for books in `stock.csv`.
Order updates are posted to kafka topic called `status`. Run the following in a separate terminal to observe the order status

```
docker-compose exec kafka kafka-console-consumer \
     --bootstrap-server kafka:9092 \
     --isolation-level read_committed \
     --from-beginning \
     --topic status
```

## Want to Customise Producer?
update `producer.py` as required and run the following commands

```
docker-compose build producer
docker-compose up producer
```
