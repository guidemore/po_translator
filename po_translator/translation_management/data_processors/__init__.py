DATAPROCESSOR_REGISTER = {}


class DataParsingError(ValueError):
    pass


class WrongProjectType(ValueError):
    pass


def data_processor_class(proj_type):
    def wrapper(cls):
        DATAPROCESSOR_REGISTER[proj_type] = cls
        return cls

    return wrapper


def get_data_processor(proj_type):
    if proj_type not in DATAPROCESSOR_REGISTER:
        raise WrongProjectType("Project type '%s' is unknown" % proj_type)
    return DATAPROCESSOR_REGISTER[proj_type]()
