import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from finops import pricing, sustainability


def test_cache_is_worth_it():
    # Break-even test: write_cost = 3.75, price_in = 3.00, read_discount = 0.10 (90% off -> save 2.70/M)
    # break_even_reads = 3.75 / 2.70 = 1.388 reads
    assert pricing.cache_is_worth_it(avg_cache_reads=2.0, write_cost_per_m=3.75, read_discount=0.10, price_in_per_m=3.00) is True
    assert pricing.cache_is_worth_it(avg_cache_reads=1.0, write_cost_per_m=3.75, read_discount=0.10, price_in_per_m=3.00) is False


def test_recommend_tier_extension():
    # Spot for interruptible non-24/7
    assert pricing.recommend_tier(hours_per_day=8, interruptible=True, gpu_type="H100") == "spot"
    # Reserved for steady high duty cycle (>= 55% -> 13.2h+)
    assert pricing.recommend_tier(hours_per_day=20, interruptible=False, gpu_type="H100", job_days=365) == "reserved"
    # On-demand for low duty cycle
    assert pricing.recommend_tier(hours_per_day=5, interruptible=False, gpu_type="A100") == "on_demand"


def test_carbon_aware_savings():
    wh = 1000.0  # 1 kWh
    c_us = sustainability.carbon_g(wh, "us-east-1")
    c_no = sustainability.carbon_g(wh, "europe-north1")
    assert c_us == 380.0
    assert c_no == 30.0
    assert (c_us - c_no) / c_us > 0.90  # >90% reduction
