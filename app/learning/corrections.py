class CorrectionService:
    def reconcile(self, previous: dict, correction: dict) -> dict:
        return {'previous_state':previous,'new_state':correction,'change_type':'correction'}
