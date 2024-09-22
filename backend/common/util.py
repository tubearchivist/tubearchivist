def catch_all_test(func):

    def wrapper(*args, **kwargs):
        print(f"Testing {func}({args}, {kwargs}) ...")
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e.__class__)
            print(e)
            raise e
        finally:
            print(f"Done testing {func} ...")

    return wrapper
