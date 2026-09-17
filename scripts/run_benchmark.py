from app.learning.benchmark import BenchmarkRunner

def main(): print(BenchmarkRunner().run([], lambda q: {'question':q}))
if __name__=='__main__': main()
