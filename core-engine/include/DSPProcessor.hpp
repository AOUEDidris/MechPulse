#pragma once
#include <vector>
#include <complex>
#include <cstdint>

class DSPProcessor {
public:
    DSPProcessor();

    // تطبيق نافذة Hanning لتقليل التسرب الطيفي (Spectral Leakage)
    void applyHanningWindow(const std::vector<float>& input, std::vector<float>& output);

    // حساب تحويل فورييه السريع (Radix-2 Cooley-Tukey FFT)
    void computeFFT(const std::vector<float>& windowed_signal, std::vector<float>& magnitude_spectrum);

    // المؤشرات الإحصائية في المجال الزمني (Time-Domain Statistical Metrics)
    float calculateRMS(const std::vector<float>& signal);
    float calculatePeak(const std::vector<float>& signal);
    float calculateCrestFactor(float peak, float rms);
    float calculateKurtosis(const std::vector<float>& signal, float mean = 0.0f);

private:
    void fftRecursive(std::vector<std::complex<float>>& a);
};
