# VLSA

**Interpretable Vision-Language Survival Analysis with Ordinal Inductive Bias for Computational Pathology**

*On updating. Paper and code will release soon. Stay tuned.*

**Abstract**: Histopathology Whole-Slide Images (WSIs) provide an important tool to assess cancer prognosis in computational pathology (CPATH). While existing survival analysis (SA) approaches have made exciting progress, they are generally limited to adopting highly-expressive architectures and only coarse-grained patient-level labels to learn prognostic visual representations from gigapixel WSIs. Such learning paradigm suffers from important performance bottlenecks, when facing present scarce training data and standard multi-instance learning (MIL) framework in CPATH. To break through it, this paper, for the first time, proposes a new Vision-Language-based SA (**VLSA**) paradigm. Concretely, (1) VLSA is driven by pathology VL foundation models. It no longer relies on high-capability networks and shows the advantage of *data efficiency*. (2) In vision-end, VLSA encodes prognostic language prior and then employs it as *auxiliary signals* to guide the aggregating of prognostic visual features at instance level, thereby compensating for the weak supervision in MIL. Moreover, given the characteristics of SA, we propose i) *ordinal survival prompt learning* to transform continuous survival labels into textual prompts; and ii) *ordinal incidence function* as prediction target to make SA compatible with VL-based prediction. VLSA's predictions can be interpreted intuitively by our Shapley values-based method. The extensive experiments on five datasets confirm the effectiveness of our scheme. Our VLSA could pave a new way for SA in CPATH by offering weakly-supervised MIL an effective means to learn valuable prognostic clues from gigapixel WSIs.

<!-- Insert a pipeline of your algorithm here if got one -->
<div align="center">
    <a href="https://"><img width="100%" height="auto" src="./docs/fig-vlsa-overview.png"></a>
</div>

---

📚 Recent updates:
- 24/09/10: release VLSA
