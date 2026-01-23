_package_name: str = "jaai-hub-custom-api"
try:
    import importlib.metadata

    __version__ = importlib.metadata.version(_package_name)
except:
    import pkg_resources

    __version__ = pkg_resources.get_distribution(_package_name).version
