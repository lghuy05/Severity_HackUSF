from specialized.contact_agent import ContactAgent


# Summary assembly now happens in `core.runner.build_response`; this shim remains for
# backwards compatibility with older imports.
summary_agent = ContactAgent()
