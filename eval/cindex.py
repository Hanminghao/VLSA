from typing import Union
import numpy as np
from torch import Tensor
from numpy import ndarray


def concordance_index(
    y_true: Union[Tensor, ndarray], 
    y_pred: Union[Tensor, ndarray],
    **kws
) -> float:
    """Concordance-index Evaluation.

    For coxph model
    Args:
        y_true (Union[Tensor, ndarray]): Observed time (at the first column) and event indicator (at the second column). 
        y_pred (Union[Tensor, ndarray]): Predicted value (proportional hazard).

    For discrete model
    Args:
        y_true (Union[Tensor, ndarray]): Observed time (at the first column) and event indicator (at the second column). 
        y_pred (Union[Tensor, ndarray]): Predicted value (time-dependent hazard function).
    """
    if isinstance(y_pred, Tensor):
        y_pred = y_pred.numpy()
    if isinstance(y_true, Tensor):
        y_true = y_true.numpy()

    if y_pred.shape[1] == 1: # coxph model if its prediction is a scalar value indicating proportional hazard
        if 'type_pred' in kws:
            assert kws['type_pred'] == 'hazard_ratio'
        y_true = np.squeeze(y_true)
        y_pred = np.squeeze(y_pred)
        t, e = y_true[:, 0], y_true[:, 1].astype(np.bool_)
        return concordance_index_censored(e, t, -y_pred, tied_tol=1e-08)[0]
    else: # discrete model
        y_t, y_e = y_true[:, 0], y_true[:, 1].astype(np.bool_)
        if 'type_pred' in kws and kws['type_pred'] == 'incidence':
            survival = 1.0 - np.cumsum(y_pred, axis=1)
        else:
            survival = np.cumprod(1.0 - y_pred, axis=1)
        risk = np.sum(survival, axis=1)
        return concordance_index_censored(y_e, y_t, -risk, tied_tol=1e-08)[0]


#######################################################################
# C-Index calculation. Its code is from package `Scikit-Survival`.
#######################################################################
import numpy
from sklearn.utils import check_array, check_consistent_length


class NoComparablePairException(ValueError):
    """An error indicating that data of censored event times
    does not contain one or more comparable pairs.
    """

def _check_estimate_1d(estimate, test_time):
    estimate = check_array(estimate, ensure_2d=False)
    if estimate.ndim != 1:
        raise ValueError(
            'Expected 1D array, got {:d}D array instead:\narray={}.\n'.format(
                estimate.ndim, estimate))
    check_consistent_length(test_time, estimate)
    return estimate

def _check_inputs(event_indicator, event_time, estimate):
    check_consistent_length(event_indicator, event_time, estimate)
    event_indicator = check_array(event_indicator, ensure_2d=False)
    event_time = check_array(event_time, ensure_2d=False)
    estimate = _check_estimate_1d(estimate, event_time)

    if not numpy.issubdtype(event_indicator.dtype, numpy.bool_):
        raise ValueError(
            'only boolean arrays are supported as class labels for survival analysis, got {0}'.format(
                event_indicator.dtype))

    if len(event_time) < 2:
        raise ValueError("Need a minimum of two samples")

    if not event_indicator.any():
        raise ValueError("All samples are censored")

    return event_indicator, event_time, estimate

def _get_comparable(event_indicator, event_time, order):
    n_samples = len(event_time)
    tied_time = 0
    comparable = {}
    i = 0
    while i < n_samples - 1:
        time_i = event_time[order[i]]
        start = i + 1
        end = start
        while end < n_samples and event_time[order[end]] == time_i:
            end += 1

        # check for tied event times
        event_at_same_time = event_indicator[order[i:end]]
        censored_at_same_time = ~event_at_same_time
        for j in range(i, end):
            if event_indicator[order[j]]:
                mask = numpy.zeros(n_samples, dtype=bool)
                mask[end:] = True
                # an event is comparable to censored samples at same time point
                mask[i:end] = censored_at_same_time
                comparable[j] = mask
                tied_time += censored_at_same_time.sum()
        i = end

    return comparable, tied_time

def _estimate_concordance_index(event_indicator, event_time, estimate, weights, tied_tol=1e-8):
    order = numpy.argsort(event_time)

    comparable, tied_time = _get_comparable(event_indicator, event_time, order)

    if len(comparable) == 0:
        raise NoComparablePairException(
            "Data has no comparable pairs, cannot estimate concordance index.")

    concordant = 0
    discordant = 0
    tied_risk = 0
    numerator = 0.0
    denominator = 0.0
    for ind, mask in comparable.items():
        est_i = estimate[order[ind]]
        event_i = event_indicator[order[ind]]
        w_i = weights[order[ind]]

        est = estimate[order[mask]]

        assert event_i, 'got censored sample at index %d, but expected uncensored' % order[ind]

        ties = numpy.absolute(est - est_i) <= tied_tol
        n_ties = ties.sum()
        # an event should have a higher score
        con = est < est_i
        n_con = con[~ties].sum()

        numerator += w_i * n_con + 0.5 * w_i * n_ties
        denominator += w_i * mask.sum()

        tied_risk += n_ties
        concordant += n_con
        discordant += est.size - n_con - n_ties

    cindex = numerator / denominator
    return cindex, concordant, discordant, tied_risk, tied_time

def concordance_index_censored(event_indicator, event_time, estimate, tied_tol=1e-8):
    """Concordance index for right-censored data
    The concordance index is defined as the proportion of all comparable pairs
    in which the predictions and outcomes are concordant.
    Two samples are comparable if (i) both of them experienced an event (at different times),
    or (ii) the one with a shorter observed survival time experienced an event, in which case
    the event-free subject "outlived" the other. A pair is not comparable if they experienced
    events at the same time.
    Concordance intuitively means that two samples were ordered correctly by the model.
    More specifically, two samples are concordant, if the one with a higher estimated
    risk score has a shorter actual survival time.
    When predicted risks are identical for a pair, 0.5 rather than 1 is added to the count
    of concordant pairs.
    See the :ref:`User Guide </user_guide/evaluating-survival-models.ipynb>`
    and [1]_ for further description.
    Parameters
    ----------
    event_indicator : array-like, shape = (n_samples,)
        Boolean array denotes whether an event occurred
    event_time : array-like, shape = (n_samples,)
        Array containing the time of an event or time of censoring
    estimate : array-like, shape = (n_samples,)
        Estimated risk of experiencing an event
    tied_tol : float, optional, default: 1e-8
        The tolerance value for considering ties.
        If the absolute difference between risk scores is smaller
        or equal than `tied_tol`, risk scores are considered tied.
    Returns
    -------
    cindex : float
        Concordance index
    concordant : int
        Number of concordant pairs
    discordant : int
        Number of discordant pairs
    tied_risk : int
        Number of pairs having tied estimated risks
    tied_time : int
        Number of comparable pairs sharing the same time
    See also
    --------
    concordance_index_ipcw
        Alternative estimator of the concordance index with less bias.
    References
    ----------
    .. [1] Harrell, F.E., Califf, R.M., Pryor, D.B., Lee, K.L., Rosati, R.A,
           "Multivariable prognostic models: issues in developing models,
           evaluating assumptions and adequacy, and measuring and reducing errors",
           Statistics in Medicine, 15(4), 361-87, 1996.
    """
    event_indicator, event_time, estimate = _check_inputs(
        event_indicator, event_time, estimate)

    w = numpy.ones_like(estimate)

    return _estimate_concordance_index(event_indicator, event_time, estimate, w, tied_tol)
