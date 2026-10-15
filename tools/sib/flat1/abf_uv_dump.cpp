// Provenance: Project HERCULES | owner the owner | [id removed]
// FLAT-1 driver: run the official volume-cartographer ABF++ flattening
// (vc::abfFlatten from libvc_flattening, villa 41701aa, unmodified) with the
// exact configuration vc_flatten uses by default, and write the per-vertex UV
// as two single-channel float32 TIFFs (u.tif, v.tif; -1 where invalid).
// Reason: `vc_flatten --uv-only` computes the same UVs but aborts when saving
// the 2-channel "uv" channel (cv::imwrite asserts channels in {1,3,4}).
// Usage: abf_uv_dump <in.tifxyz> <out_dir> [iterations=10] [lscm_only=0] [scale_to_area=1]
#include "vc/core/util/QuadSurface.hpp"
#include "vc/flattening/ABFFlattening.hpp"
#include <opencv2/imgcodecs.hpp>
#include <filesystem>
#include <iostream>
#include <string>

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "usage: abf_uv_dump <in.tifxyz> <out_dir> [iterations] [lscm_only] [scale_to_area]\n";
        return 2;
    }
    vc::ABFConfig config;  // defaults as in vc_flatten.cpp
    config.maxIterations = argc > 3 ? static_cast<std::size_t>(std::stoi(argv[3])) : 10;
    config.downsampleFactor = 1;
    config.useABF = !(argc > 4 && std::stoi(argv[4]) != 0);
    config.scaleToOriginalArea = !(argc > 5 && std::stoi(argv[5]) == 0);
    auto surf = load_quad_from_tifxyz(argv[1]);
    if (!surf) { std::cerr << "load failed\n"; return 1; }
    cv::Mat_<cv::Vec2f> uv = vc::abfFlatten(*surf, config);
    if (uv.empty()) { std::cerr << "abfFlatten failed\n"; return 1; }
    std::vector<cv::Mat> ch;
    cv::split(uv, ch);
    std::filesystem::create_directories(argv[2]);
    const std::string d = argv[2];
    if (!cv::imwrite(d + "/u.tif", ch[0]) || !cv::imwrite(d + "/v.tif", ch[1])) {
        std::cerr << "write failed\n"; return 1;
    }
    std::cout << "abf_uv_dump: wrote " << uv.cols << " x " << uv.rows << " uv, iterations="
              << config.maxIterations << " useABF=" << config.useABF
              << " scaleToOriginalArea=" << config.scaleToOriginalArea << std::endl;
    return 0;
}
