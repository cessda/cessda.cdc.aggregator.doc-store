# syntax=docker/dockerfile:1
#
# Updated dockerfile syntax is required for --mount option
#
# Declares a two-stage build that initially builds all python
# packages and installs them into .local in the first stage.
# Then use another stage to actually create the image without
# temporary files or git by copying .local from first stage
# and prepending it to PATH.
#
#
# Building the image
# ##################
#
# The build needs credentials to access Bitbucket. It uses
# --secret option, which is a feature provided by buildkit.
# The secret is expected to be accessible within the build-
# container via id 'bbcreds'. See buildkit manual on how to
# pass the secret to the build.
#
# Example with a mysecret-file:
#
# $ echo bbhandle:passw0rd > mysecret
# $ DOCKER_BUILDKIT=1 docker build \
#     -t "cdcagg-docstore" \
#     --secret id=bbcreds,src=mysecret .
#
#
# Running the container - DBAdmin
# ###############################
#
# The container has a built-in dbadmin-module to help setup
# a compatible MongoDB replicaset. See module documentation
# for a complete command reference.
#
# Example command to run the DBAdmin initial setup process:
#
# $ docker run \
#     --name "cdcagg_dbadmin_initial_setup"
#     -e "CDCAGG_DBREPLICAS=[153.1.61.74:27017, 153.1.61.74:27018, 153.1.61.74:27019]" \
#     -e "CDCAGG_DBUSER_ADMIN=rootadmin" \
#     -e "CDCAGG_DBPASS_ADMIN=password" \
#     cdcagg-docstore \
#     cdcagg_docstore.db_admin \
#     initiate_replicaset setup_database setup_collections setup_users
#
#
# Running the container - Document Store
# ######################################
#
# Container needs to expose port 6001 to host machine.
# CDCAGG_BDREPLICAS environment variable should contain
# a list of MongoDB replicas that are configured with
# cdcagg_docstore.db_admin.
#
# Example command to start serving the Document Store:
#
# $ docker run \
#     --name "cdcagg_docstore" \
#     -p 5001:6001 \
#     -e "CDCAGG_DBREPLICAS=[153.1.61.74:27017, 153.1.61.74:27018, 153.1.61.74:27019]" \
#     cdcagg-docstore

FROM python:3.11-slim as builder

COPY . /docker-build
WORKDIR /docker-build

RUN apt-get update \
  && apt-get install git -y \
  && apt-get clean

# Expects 'bbcreds'-secret.

RUN --mount=type=secret,id=bbcreds \
  BBCREDS=$(cat /run/secrets/bbcreds) \
  pip install --user -r requirements.txt \
  && pip install --user .


# END FIRST STAGE


FROM python:3.11-slim as prod

# Copy build packages from builder image to prod.
# Add them to PATH.

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

CMD ["cdcagg_docstore"]

ENTRYPOINT ["python", "-m"]
