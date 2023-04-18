import calendar
from datetime import datetime
from rest_framework.throttling import ScopedRateThrottle


class MonthlyScopedRateThrottle(ScopedRateThrottle):
    def parse_rate(self, rate):
        """
        Given the request rate string, return a two tuple of:
        <allowed number of requests>, <period of time in seconds>
        """
        if rate is None:
            return (None, None)
        num, period = rate.split('/')
        num_requests = int(num)
        if period.startswith('mo'):
            now = datetime.now()
            _, days_in_month = calendar.monthrange(now.year, now.month)
            duration = days_in_month * 24 * 60 * 60
        elif period.startswith('mi'):
            duration = 60
        else:
            duration = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period[0]]
        return (num_requests, duration)


class SubscriptionRateThrottle(MonthlyScopedRateThrottle):
    def allow_request(self, request, view):
        # Only throttle POST requests
        if request.method != 'POST':
            return True
        
        # Get the subscription level of the user, e.g. from a UserProfile model
        subscription_plan = request.user.plan.name
        
        # Define the default throttle rates based on the subscription plan
        throttle_rates = {
            'free': {
                'snippets_limit': '5/month',
                'summaries_limit': '5/month',
            },
            'basic': {
                'snippets_limit': '30/month',
                'summaries_limit': '20/month',
            },
            'premium': {
                'snippets_limit': '300/month',
                'summaries_limit': '100/month',
            },
            'admin': {
                'snippets_limit': '9999/month',
                'summaries_limit': '999/month',
            },
        }
        
        # Get the throttle rate for the user's subscription level and the current scope
        throttle_rate = throttle_rates[subscription_plan].get(self.scope, None)
        
        # If there is no throttle rate for the current scope, use the default rate
        if throttle_rate is None:
            return True
        
        # Set the throttle rate for the current scope using the MonthlyScopedRateThrottle class
        self.rate = throttle_rate

        # Call the parent allow_request method with the custom throttle rate
        return super().allow_request(request, view)
