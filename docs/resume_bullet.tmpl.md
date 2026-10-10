# Resume bullet (measured results only)

_Rendered from `resume_bullet.tmpl.md`; every number is a ledger value._

- Built a pre-registered mineral prospectivity study on USGS NURE stream-sediment geochemistry and MRDS gold producers over Nevada ({{labels.n_cells}} grid cells, {{prep.n_samples}} samples, {{labels.n_positive_sites}} producer sites): compositional log-ratio features, two models under random and spatial block cross-validation with repeated allocations, and a frozen decision rule. Showed that random k-fold overstated the boosted model's AUC ({{cv.hgb.random.auc.mean:.3f}} versus {{cv.hgb.ref.auc.mean:.3f}} with {{headline.reference_block_km:g}} km blocks chosen from the target's autocorrelation range) and that the laboratory was learnable (leave-one-family-out AUC {{batch.hgb.lofo.auc:.3f}}); every reported number is traceable from extract to script to ledger to report through a verification harness with a clean re-execution.
