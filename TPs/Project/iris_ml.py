from pandas import read_csv
from pyspark import SparkConf,      \
                    SparkContext,   \
                    SparkFiles
from pyspark.sql import SQLContext, Row
from pyspark.ml import Pipeline
from pyspark.ml.linalg import Vectors
from pyspark.ml.feature import StringIndexer,   \
                               VectorAssembler, \
                               StandardScaler
from pyspark.ml.classification import DecisionTreeClassifier,   \
                                      LogisticRegression,   \
                                      NaiveBayes
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

# App Environment
MASTER_URL  = "spark://front-in1.cemef:7077"
APP_NAME    = "IRIS-ML"
DATA_DIR    = "/gext/rami.kader/hpcai/HPDA/BigDataHadoopSparkDaskCourse/TPs/Project/iris.csv"

# Spark Context & Conf
print("Setting Spark Context...")
conf        = SparkConf().setMaster(MASTER_URL).setAppName(APP_NAME)
sc          = SparkContext(conf=conf)
sc.setLogLevel("ERROR")
sqlContext  = SQLContext(sc)

# Data Load & Setup
print("Loading data...")
iris_df     = sqlContext.createDataFrame(read_csv(DATA_DIR))

# Add a transformer for features assembly into models supported format
transformer = VectorAssembler(
    inputCols=["sepal_length",
               "sepal_width",
               "petal_length",
               "petal_width"],
    outputCol="features")

# Add a numeric indexer for the label/target column
labellizer = StringIndexer(inputCol="variety", outputCol="label")

# Add a gaussian-normalizor for features set
scaler = StandardScaler(
    inputCol="features",
    outputCol="scaled",
    withStd=True, withMean=True)

# Split into training and testing data
(trainingData, testData) = iris_df.randomSplit([0.75, 0.25])

# Create the models
dtClass     = DecisionTreeClassifier(
    labelCol="label",
    featuresCol="scaled",
    maxDepth=5)
nvbClass    = NaiveBayes(
    labelCol="label",
    featuresCol="scaled",
    smoothing=0.5,
    modelType="gaussian")
lrClass     = LogisticRegression(
    labelCol="label",
    featuresCol="scaled",
    maxIter=15)

# ML-Pipelines
print("Creating training pipelines...")
dtPipe  = Pipeline(stages=[transformer, labellizer, scaler, dtClass])
nvbPipe = Pipeline(stages=[transformer, labellizer, scaler, nvbClass])
lrPipe  = Pipeline(stages=[transformer, labellizer, scaler, lrClass])

# Models objects output
print("Fitting pipelines...")
dtModel     = dtPipe.fit(trainingData)
nvbModel    = nvbPipe.fit(trainingData)
lrModel     = lrPipe.fit(trainingData)

# Predict on the test data
print("Performing predictions...")
dt_predictions  = dtModel.transform(testData)
nvb_predictions = nvbModel.transform(testData)
lr_predictions  = lrModel.transform(testData)

# Evaluate accuracy
evaluator = MulticlassClassificationEvaluator(
    predictionCol="prediction",
    labelCol="label",
    metricName="accuracy")
print("\n--- Classifiers Test Errors ---")
print("Decision Tree: %g " % (1.0 - evaluator.evaluate(dt_predictions)))
print("Naive Bayes: %g " % (1.0 - evaluator.evaluate(nvb_predictions)))
print("Logistic Regression: %g " % (1.0 - evaluator.evaluate(lr_predictions)))

# Closing Spark Context
sc.stop()