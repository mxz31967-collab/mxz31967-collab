import sys,unittest,json,copy
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import update, steam, art

class BehaviourTests(unittest.TestCase):
    def test_free_to_keep_is_not_free_trial_or_f2p(self):
        template='<div class="game_area_purchase_game"><p class="game_purchase_discount_quantity">{}</p><div>-100%</div></div>'
        self.assertTrue(steam.purchase_offer(template.format('在某日之前获取，即可免费保留。'),'keep'))
        self.assertIsNone(steam.purchase_offer(template.format('免费周末！仅可试玩两天'),'keep'))
        self.assertIsNone(steam.purchase_offer(template.format('免费开玩'),'keep'))
    def test_broken_source_does_not_mean_no_offers(self):
        old={'success_at':'昨天','offers':[{'id':'123'}]}
        def failed():raise ValueError('changed')
        new=steam.update_section(old,failed,'今天')
        self.assertFalse(new['ok']);self.assertEqual(new['offers'],old['offers'])
        self.assertEqual(new['success_at'],'昨天')
        recovered=steam.update_section(new,lambda:[],'明天')
        self.assertTrue(recovered['ok']);self.assertEqual(recovered['offers'],[])
    def test_search_accepts_only_discount_and_steam_app(self):
        payload={'total_count':3,'results_html':'''<a class="search_result_row" href="https://store.steampowered.com/app/123/test/"><div class="discount_pct">-100%</div></a><a class="search_result_row" href="https://evil.test/app/456/"><div class="discount_pct">-100%</div></a><a class="search_result_row" href="https://store.steampowered.com/app/789/"><div class="discount_pct">-50%</div></a>'''}
        self.assertEqual(steam.parse_search(payload),['123'])
    def test_featured_paid_sale_not_trial(self):
        data={'specials':{'items':[{'id':10,'type':0,'name':'Play for free this weekend'},{'id':11,'type':0,'name':'Weekend deal','discount_percent':70}]}}
        self.assertEqual(list(steam.trial_candidates(data)),['10'])
    def test_permanent_f2p_is_not_a_weekend_offer(self):
        item={'name':'Play for free'}
        self.assertFalse(steam.is_limited_trial(item,{'is_free':True}))
        self.assertTrue(steam.is_limited_trial(item,{'price_overview':{'initial':5000}}))
        self.assertTrue(steam.is_limited_trial({'name':'Free Weekend'},{}))
    def test_once_per_beijing_day_and_feed_limit(self):
        first=update.daily_frog({},'2026-09-16')
        repeat=update.daily_frog(first,'2026-09-16')
        self.assertEqual(first,repeat)
        fed=update.daily_frog(first,'2026-09-16','喂小呱')
        again=update.daily_frog(fed,'2026-09-16','喂小呱')
        self.assertEqual(fed['energy'],again['energy']);self.assertEqual(len(again['history']),1)
        self.assertNotIn('fed_day',first)
    def test_next_day_rest_and_cancel(self):
        f=update.daily_frog({},'2026-09-16','明天休息')
        rest=update.daily_frog(f,'2026-09-17')
        self.assertTrue(rest['history'][-1]['rest']);self.assertEqual(rest['travel_count'],1)
        f=update.daily_frog(f,'2026-09-16','明天出发')
        trip=update.daily_frog(f,'2026-09-17')
        self.assertFalse(trip['history'][-1]['rest']);self.assertEqual(trip['travel_count'],2)
    def test_pet_survives_unattended_and_missed_days(self):
        f={}
        for day in range(1,30):f=update.daily_frog(f,f'2026-09-{day:02}')
        self.assertGreaterEqual(f['energy'],0);self.assertLessEqual(f['energy'],100)
        self.assertTrue(any(x['rest'] for x in f['history']))
        resumed=update.daily_frog(f,'2026-11-01')
        self.assertEqual(len(resumed['history']),30)
    def test_box_no_repeats_and_same_day_is_stable(self):
        pool=[{'url':'https://example.com/'+str(i)} for i in range(3)]
        b={};urls=[]
        for i in range(3):
            day=f'2026-09-{i+1:02}';b=update.daily_box(b,day,pool);urls.append(b['site']['url'])
            self.assertEqual(update.daily_box(b,day,pool),b)
        self.assertEqual(len(set(urls)),3)
        self.assertEqual(len(update.daily_box(b,'2026-09-04',pool)['cycle_used']),1)
    def test_svg_escapes_labels_and_is_valid(self):
        import xml.etree.ElementTree as ET
        f=update.daily_frog({},'2026-09-16');e=f['history'][-1]
        for source in (art.postcard(e,1,72),art.hero(),art.footprints(f['history'])):ET.fromstring(source)
        self.assertNotIn('<script>',art.text(0,0,'<script>bad</script>'))
    def test_markdown_game_content_is_escaped(self):
        s=update.section('测试',{'ok':True,'checked_at':'今天','offers':[{'id':'1','kind':'keep','name':'<script>bad</script>','note':'<img src=x>'}]})
        self.assertNotIn('<script>',s);self.assertNotIn('<img src=x>',s)

if __name__=='__main__':unittest.main()
