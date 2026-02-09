class DuplicateEmailError(Exception):
    def __init__(self, message="Email already registered"):
        self.message = message
        super().__init__(self.message)


class DuplicatePhoneError(Exception):
    def __init__(self, message="Phone number already registered"):
        self.message = message
        super().__init__(self.message)


class ContentExtractionError(Exception):
    """
    Content extraction exception
    """

    def __init__(self, message="Content extraction failed"):
        self.message = message
        super().__init__(self.message)
