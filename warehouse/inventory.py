import csv
import ast


class Inventory:
    def __init__(self, location):
        self.inventory = location

    def add_stock(self, isbn, stock):
        books = list()
        with open(self.inventory) as in_file:
            reader = csv.reader(in_file)
            books = list(reader)

        with open(self.inventory, "w", newline = '') as out_file:
            writer = csv.writer(out_file)

            for row in books:
                if row[0] == isbn:
                    in_stock = ast.literal_eval(row[2])
                    row[2] = in_stock + stock
                writer.writerow(row)

    def get_stock(self, isbn) -> int:
        in_stock = 0
        with open(self.inventory, "r") as in_file:
            reader = csv.reader(in_file)
            for row in reader:
                if row[0] == isbn:
                    in_stock = ast.literal_eval(row[2])
                    break
        return in_stock

    def get_value(self, isbn) -> float:
        value = 0.0
        with open(self.inventory, "r") as in_file:
            reader = csv.reader(in_file)
            for row in reader:
                if row[0] == isbn:
                    value = ast.literal_eval(row[4])
                    break
        return value

    def mark_sold(self, isbn) -> int:
        books = list()
        with open(self.inventory, "r") as in_file:
            reader = csv.reader(in_file)
            books = list(reader)

        with open(self.inventory, "w", newline = '') as out_file:
            writer = csv.writer(out_file)

            in_stock = 0
            for row in books:
                if row[0] == isbn:
                    in_stock = ast.literal_eval(row[2])
                    sold = ast.literal_eval(row[3])
                    if in_stock >= 1:
                        row[2] = in_stock - 1
                        row[3] = sold + 1
                        in_stock = in_stock - 1
                writer.writerow(row)

            return in_stock