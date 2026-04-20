import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';
import 'storage_service.dart';

class AdsService {
  static const _testBanner = 'ca-app-pub-3940256099942544/6300978111';
  static const _testInterstitial = 'ca-app-pub-3940256099942544/1033173712';
  static const _testRewarded = 'ca-app-pub-3940256099942544/5224354917';

  static InterstitialAd? _interstitial;
  static RewardedAd? _rewarded;
  static int _matchesSinceInterstitial = 0;
  static bool _initialized = false;

  static String get banner => _testBanner;

  static bool get adsRemoved => StorageService.getBool(StorageKeys.removeAds);

  static Future<void> init() async {
    if (adsRemoved) return;
    try {
      await MobileAds.instance.initialize();
      _initialized = true;
      _loadInterstitial();
      _loadRewarded();
    } catch (e) {
      debugPrint('Ads init failed: $e');
    }
  }

  static void _loadInterstitial() {
    if (!_initialized || adsRemoved) return;
    InterstitialAd.load(
      adUnitId: _testInterstitial,
      request: const AdRequest(),
      adLoadCallback: InterstitialAdLoadCallback(
        onAdLoaded: (ad) => _interstitial = ad,
        onAdFailedToLoad: (e) {
          debugPrint('Interstitial failed: $e');
          _interstitial = null;
        },
      ),
    );
  }

  static void _loadRewarded() {
    if (!_initialized) return;
    RewardedAd.load(
      adUnitId: _testRewarded,
      request: const AdRequest(),
      rewardedAdLoadCallback: RewardedAdLoadCallback(
        onAdLoaded: (ad) => _rewarded = ad,
        onAdFailedToLoad: (e) {
          debugPrint('Rewarded failed: $e');
          _rewarded = null;
        },
      ),
    );
  }

  static Future<void> maybeShowInterstitial() async {
    if (adsRemoved) return;
    _matchesSinceInterstitial++;
    if (_matchesSinceInterstitial < 2) return;
    final ad = _interstitial;
    if (ad == null) {
      _loadInterstitial();
      return;
    }
    ad.fullScreenContentCallback = FullScreenContentCallback(
      onAdDismissedFullScreenContent: (ad) {
        ad.dispose();
        _interstitial = null;
        _matchesSinceInterstitial = 0;
        _loadInterstitial();
      },
      onAdFailedToShowFullScreenContent: (ad, err) {
        ad.dispose();
        _interstitial = null;
        _loadInterstitial();
      },
    );
    await ad.show();
  }

  static Future<bool> showRewarded({required Function(int) onReward}) async {
    final ad = _rewarded;
    if (ad == null) {
      _loadRewarded();
      return false;
    }
    final completer = Completer<bool>();
    bool earned = false;
    ad.fullScreenContentCallback = FullScreenContentCallback(
      onAdDismissedFullScreenContent: (ad) {
        ad.dispose();
        _rewarded = null;
        _loadRewarded();
        if (!completer.isCompleted) completer.complete(earned);
      },
      onAdFailedToShowFullScreenContent: (ad, err) {
        ad.dispose();
        _rewarded = null;
        _loadRewarded();
        if (!completer.isCompleted) completer.complete(false);
      },
    );
    ad.show(onUserEarnedReward: (ad, reward) {
      earned = true;
      onReward(reward.amount.toInt());
    });
    return completer.future;
  }
}
