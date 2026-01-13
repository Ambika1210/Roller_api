import responseStatus from '../constants/responseStatus.json' with { type: 'json' };
import responseData from '../constants/responseData.json' with { type: 'json' };

export function setSuccess(res, data) {
  res.status(responseStatus.STATUS_SUCCESS_OK);
  res.json({ status: responseData.SUCCESS, data });
}
export function setCreateSuccess(res, data) {
  res.status(responseStatus.STATUS_SUCCESS_CREATED);
  res.json({ status: responseData.SUCCESS, data });
}

export function setNotAuthorized(res, data) {
  res.status(responseStatus.NOT_AUTHORIZED);
  res.json({ status: responseData.ERROR, data });
}

export function setNotFoundError(res, data) {
  res.status(responseStatus.NOT_FOUND);
  res.json({ status: responseData.ERROR, data });
}

export function setForbidden(res, data) {
  res.status(responseStatus.FORBIDDEN);
  res.json({ status: responseData.ERROR, data });
}
export function setBadRequest(res, data) {
  res.status(responseStatus.BAD_REQUEST);
  res.json({ status: responseData.ERROR, data });
}
export function setConflictError(res, data) {
  res.status(responseStatus.CONFLICT);
  res.json({ status: responseData.ERROR, data });
}
export function setServerError(res, data) {
  res.status(responseStatus.INTERNAL_SERVER_ERROR);
  res.json({ status: responseData.ERROR, data });
}

export function createResponseSetter(moduleName) {
  return function setResponse(req, res, err, model) {
    if (err) {
      setServerError(res, `Error occured: ${err}`);
    } else {
      const module = model[moduleName];
      if (module) {
        setSuccess(res, { moduleName: module });
      } else {
        setNotFoundError(res, `${moduleName}: ${req.params.id} not found`);
      }
    }
  };
}
