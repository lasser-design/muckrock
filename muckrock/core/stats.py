"""
Utilities for calculating stats for agencies and jurisdictions
"""

# Django
from django.db.models import Count

def collect_stats(obj, context):
    """Helper for collecting stats"""
    statuses = ("rejected", "ack", "processed", "fix", "no_docs", "done", "appealing")
    requests = obj.get_requests()
    status_counts = (
        requests.filter(status__in=statuses)
        .order_by("status")
        .values_list("status")
        .annotate(Count("status"))
    )
    context.update({"num_%s" % s: c for s, c in status_counts})
    context["num_overdue"] = requests.get_overdue().count()
    context["num_submitted"] = requests.count()

def assign_grade(grade, text):
    return {
        "grade": grade,
        "text": text
    }

def grade_agency(agency, context):
    """Score the agency based on relative stats"""
    context["grades"] = {
        "abs_response_time": grade_absolute_response_time(agency),
        "rel_response_time": grade_relative_response_time(agency),
        "success_rate": grade_success_rate(agency),
    }

def grade_absolute_response_time(agency):
    """Do they respond within the legally allowed time?"""
    if (agency.jurisdiction.days >= agency.average_response_time()):
        return assign_grade(
            "pass",
            "On average, they respond within the legally allowed time."
        )
    else:
        return assign_grade(
            "fail",
            "On average, they take longer to respond than allowed by law."
        )

def grade_relative_response_time(agency):
    """Do they respond faster than other agencies in the jurisdiction?"""
    agency_average_response_time = agency.average_response_time()
    jurisdiction_average_response_time = agency.jurisdiction.average_response_time()
    if (agency_average_response_time == 0 or jurisdiction_average_response_time == 0):
        return assign_grade(
            "neutral",
            "Not enough data available to evaluate agency"
        )
    elif (agency_average_response_time <= jurisdiction_average_response_time):
        percentile = (1 - (agency_average_response_time / jurisdiction_average_response_time)) * 100
        return assign_grade("pass", "They typically respond {}% faster than other agencies in their jurisdiction".format(percentile))
    else:
        percentile = ((agency_average_response_time / jurisdiction_average_response_time) - 1) * 100
        return assign_grade("fail", "They typically respond {}% slower than other agencies in their jurisdiction".format(percentile))
    
def grade_success_rate(agency):
    """Do they fulfill requests more than other agencies in the jurisdiction?"""
    agency_success_rate = agency.success_rate()
    jurisdiction_success_rate = agency.jurisdiction.success_rate()
    if (jurisdiction_success_rate == 0 or agency_success_rate == 0):
        return assign_grade(
            "neutral",
            "Not enough data available to evaluate agency"
        )
    elif (agency_success_rate >= jurisdiction_success_rate):
        percentile = ((agency_success_rate / jurisdiction_success_rate) - 1) * 100
        return assign_grade(
            "pass",
            "They fulfill {}% more requests than other agencies in their jurisdiction.".format(percentile)
        )
    else:
        percentile = (1 - (agency_success_rate / jurisdiction_success_rate)) * 100
        return assign_grade(
            "fail",
            "They fulfill {}% fewer requests than other agencies in their jurisdiction.".format(percentile)
        )