
import os
import sys

# Ensure Spark uses the Python interpreter in our virtual environment
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("ResponsibleWebDataCuration")
    .master("local[2]")
    .config("spark.pyspark.python", sys.executable)
    .config("spark.pyspark.driver.python", sys.executable)
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

print("Spark Version:", spark.version)
print("Python Interpreter:", sys.executable)

# Test actual Python worker execution
numbers = spark.sparkContext.parallelize([1, 2, 3, 4, 5], 2)
squares = numbers.map(lambda x: x * x).collect()

print("Distributed Python computation:", squares)

# Test DataFrame creation
data = [
    (1, "First sample web document"),
    (2, "Second sample web document"),
    (3, "Third sample web document"),
    (4, "Fourth sample web document"),
    (5, "Fifth sample web document")
]

df = spark.createDataFrame(data, ["id", "text"])

df.show(truncate=False)

print("Total documents:", df.count())

spark.stop()
print("SPARK TEST COMPLETED SUCCESSFULLY")
