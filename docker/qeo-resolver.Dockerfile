# Scoped patch image: retain the exact deployed Dewey 8.0.2 dependency/runtime base.
FROM 108782052779.dkr.ecr.us-west-2.amazonaws.com/dayhoff/day/dewey@sha256:0780a42dd2b3d5620de2c538cada32acd661f5be5a0f0b60a08c9f941ea3af42

COPY --chown=lsmc:lsmc dewey_service/app.py dewey_service/settings.py dewey_service/qeo_package_contract.py dewey_service/qeo_resolver_auth.py /app/dewey_service/
COPY --chown=lsmc:lsmc dewey_service/cli/_service.py dewey_service/cli/qeo.py /app/dewey_service/cli/
COPY --chown=lsmc:lsmc dewey_service/services/artifact_sets.py /app/dewey_service/services/
