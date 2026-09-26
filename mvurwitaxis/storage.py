import logging

from whitenoise.storage import CompressedManifestStaticFilesStorage


logger = logging.getLogger(__name__)


class LenientManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    def hashed_name(self, name, content=None, filename=None):
        try:
            return super().hashed_name(name, content, filename)
        except ValueError:
            logger.warning(
                "Static file '%s' is missing from the staticfiles manifest - "
                "serving unhashed. Run collectstatic to fix.",
                name,
            )
            return name
