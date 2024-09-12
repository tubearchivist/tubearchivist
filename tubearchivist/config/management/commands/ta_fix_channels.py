"""
channel fix for update from v0.4.7 to v0.4.8
reindex channels with 0 subscriber count
python manage.py ta_fix_channels
"""

from django.core.management.base import BaseCommand
from home.src.es.connect import IndexPaginate
from home.tasks import check_reindex


class Command(BaseCommand):
    """fix comment link"""

    def handle(self, *args, **options):
        """run command"""
        self.stdout.write("reindex failed channels")
        channels = self._get_channels()
        if not channels:
            self.stdout.write("did not find any failed channels")
            return

        self.stdout.write(f"add {len(channels)} channels(s) to queue")
        to_reindex = {"channel": [i["channel_id"] for i in channels]}
        check_reindex.delay(data=to_reindex)
        self.stdout.write(self.style.SUCCESS("    ✓ task queued\n"))

    def _get_channels(self):
        """get failed channels"""
        self.stdout.write("search for failed channels")
        es_query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"channel_subs": {"value": 0}}},
                        {"term": {"channel_active": {"value": True}}},
                    ]
                },
            },
            "_source": ["channel_id"],
        }
        channels = IndexPaginate("ta_channel", es_query).get_results()

        return channels
