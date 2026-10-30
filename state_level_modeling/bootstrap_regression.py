"""Fit the paper's 38-state OLS model or generate real Bootstrap-Lasso logs."""
from pathlib import Path
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.linear_model import Lasso
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor

_RELEASE_ROOT = Path(__file__).resolve().parents[1]
if str(_RELEASE_ROOT) not in sys.path:
    sys.path.insert(0, str(_RELEASE_ROOT))
from runtime_config import project_path

N_BOOTSTRAPS = 10000
LASSO_ALPHA = 0.1
EPS = 1e-6
EXCLUDED_STATES = ("Connecticut", "Delaware")
FINAL_OUTPUTS = (
    "7变量38州_asinh_全州明细.csv",
    "7变量38州_asinh_指标.csv",
    "7变量38州_asinh_系数.csv",
    "7变量38州_asinh_标准化参数.csv",
    "7变量38州_asinh_OLS报告.txt",
    "7变量38州_asinh_模型定义.json",
    "最终38州模型_S10指标.csv",
)
BOOTSTRAP_OUTPUTS = (
    "Variable_Selection_Raw_Log.csv",
    "Bootstrap_OOB_Statistics.csv",
    "Bootstrap_Selection_Frequencies.csv",
    "Bootstrap_Model_Definition.json",
)


def prepare_output(out, names):
    """Create an output directory without replacing existing result files."""
    out = Path(out)
    existing = [str(out / name) for name in names if (out / name).exists()]
    if existing:
        raise FileExistsError(
            "Choose a new --output-dir; result files already exist: "
            + ", ".join(existing)
        )
    out.mkdir(parents=True, exist_ok=True)
    return out


def prepare_state_data(state_file):
    """Use the paper's fixed 30-feature, 38-state final-model specification.

    The input already contains the selected 30 interaction features. The
    historical Cook-screening result is reused by excluding the two named states.
    """
    df = pd.read_csv(state_file).set_index("State")
    features = df.columns[3:]
    if len(features) != 30 or not df.columns.is_unique:
        raise ValueError("Expected 30 distinct feature columns after the metadata.")
    if len(df) != 50 or df.index.nunique() != 50:
        raise ValueError("Expected one record for each of the 50 study states.")
    counts = df[features].to_numpy(dtype=float)
    if not np.isfinite(counts).all() or (counts < 0).any():
        raise ValueError("Interaction counts must be finite and nonnegative.")
    margin = df["Republican Vote Percentage"] - df["Democratic Vote Percentage"]
    if not np.isfinite(margin.to_numpy(dtype=float)).all():
        raise ValueError("Vote percentages must be finite.")
    y = np.arcsinh(margin)
    middle = y.sort_values().index[5:45]
    if not set(EXCLUDED_STATES).issubset(middle):
        raise ValueError("The middle 40 states must include Connecticut and Delaware.")
    sample = middle.drop(list(EXCLUDED_STATES))
    logs = np.log(df[features] + EPS)
    clr = logs.sub(logs.mean(axis=1), axis=0)
    scaler = StandardScaler().fit(clr.loc[sample])
    z = pd.DataFrame(scaler.transform(clr), index=df.index, columns=clr.columns)
    return df, features, margin, y, sample, scaler, z


def read_bootstrap_log(path, features):
    """Read selected coefficients; unselected features must be empty/NaN."""
    records = pd.read_csv(path)
    records = records.loc[records["Iteration"].notna()].copy()
    if len(records) != N_BOOTSTRAPS or records["Iteration"].nunique() != N_BOOTSTRAPS:
        raise ValueError("Expected 10,000 distinct valid Bootstrap iterations.")
    records.loc[:, features] = records.loc[:, features].apply(
        pd.to_numeric, errors="raise"
    )
    coefficients = records.loc[:, features].to_numpy(dtype=float)
    if np.isinf(coefficients).any():
        raise ValueError("Bootstrap coefficients must be finite or empty/NaN.")
    return records


def calculate(state_file, bootstrap_log, out):
    """Reconstruct the final OLS model from the existing Bootstrap log."""
    df, features, margin, y, sample, scaler, z = prepare_state_data(state_file)
    records = read_bootstrap_log(bootstrap_log, features)
    frequencies = records[features].notna().sum().sort_values(ascending=False)
    seven = frequencies.index[frequencies / len(records) > 0.5].tolist()
    if len(seven) != 7:
        raise ValueError("The paper's final model requires seven stable predictors.")
    out = prepare_output(out, FINAL_OUTPUTS)

    design=sm.add_constant(z[seven])
    fit=sm.OLS(y.loc[sample],design.loc[sample]).fit()

    fitted_y=fit.predict(design)

    fitted_margin=np.sinh(fitted_y)
    data=pd.DataFrame({'State':df.index,'actual_margin_pp':margin.to_numpy(),
                       'actual_asinh':y.to_numpy(),'fitted_asinh':fitted_y.to_numpy(),
                       'predicted_margin_pp':fitted_margin.to_numpy(),'in_fit_38':df.index.isin(sample)})

    data['error_pp']=data.predicted_margin_pp-data.actual_margin_pp
    data['absolute_error_pp']=data.error_pp.abs()
    data['direction_match']=np.sign(data.predicted_margin_pp)==np.sign(data.actual_margin_pp)
    data['outside100']=data.predicted_margin_pp.abs()>100


    rows=[]
    for group,idx in [('all_50',df.index),('fit_38',sample),('other_12',df.index.difference(sample))]:
        a,h=margin.loc[idx],fitted_margin.loc[idx]
        rows.append({'model':'7 variables, 38-state asinh OLS','sample':group,'n_states':len(idx),
                     'MAE_pp':float((h-a).abs().mean()),'RMSE_pp':float(np.sqrt(np.mean((h-a)**2))),
                     'direction_matches':int((np.sign(a)==np.sign(h)).sum()),
                     'outside100':int((h.abs()>100).sum()),
                     'r2_asinh':float(r2_score(y.loc[idx],fitted_y.loc[idx]))})
    metrics=pd.DataFrame(rows)

    ci=fit.conf_int()
    coefficients=pd.DataFrame({'term':fit.params.index,'coefficient':fit.params.to_numpy(),
                               'standard_error':fit.bse.to_numpy(),'P':fit.pvalues.to_numpy(),
                               'CI95_lower':ci[0].to_numpy(),'CI95_upper':ci[1].to_numpy()})
    for table,name in [(data.sort_values('actual_margin_pp'),'7变量38州_asinh_全州明细.csv'),
                       (metrics,'7变量38州_asinh_指标.csv'),(coefficients,'7变量38州_asinh_系数.csv')]:
        table.to_csv(out/name,index=False,encoding='utf-8-sig',float_format='%.15g')
    pd.DataFrame({'feature':features,'mean38':scaler.mean_,'scale38':scaler.scale_}).to_csv(
        out/'7变量38州_asinh_标准化参数.csv',index=False,encoding='utf-8-sig',float_format='%.15g')
    (out/'7变量38州_asinh_OLS报告.txt').write_text(fit.summary().as_text(),encoding='utf-8')
    model_info={'fit_states':sample.tolist(),'seven_features':seven,'CLR_dimensions':30,'pseudocount':1e-6,
                'scaling':'38-state StandardScaler','outcome':'asinh(Republican minus Democratic margin)',
                'inverse':'sinh','fit_R2':fit.rsquared,'fit_adjusted_R2':fit.rsquared_adj,
                'fit_F':fit.fvalue,'fit_F_P':fit.f_pvalue,'no_new_bootstrap':True,'original_Cook_excluded_states':['Connecticut','Delaware'],
                'wrong_direction_states':data.loc[~data.direction_match,'State'].tolist(),
                'outside100_states':data.loc[data.outside100,'State'].tolist()}
    (out/'7变量38州_asinh_模型定义.json').write_text(json.dumps(model_info,ensure_ascii=False,indent=2),encoding='utf-8')


    bootstrap_rows=[]
    for term in seven:

        selected=records[term].dropna()

        mean=float(selected.mean())
        agreeing=int((np.sign(selected)==np.sign(mean)).sum())
        a,b=term.split('-')
        bootstrap_rows.append({'term':term,'label':a.capitalize()+' - '+b,
            'coefficient':float(fit.params[term]),'selection_count':len(selected),
            'bootstrap_total':len(records),'selection_frequency':len(selected)/len(records),
            'conditional_bootstrap_mean':mean,'direction_consistent_count':agreeing,

            'direction_consistency':agreeing/len(selected),
            'VIF':variance_inflation_factor(design.loc[sample].to_numpy(),design.columns.get_loc(term))})
    pd.DataFrame(bootstrap_rows).to_csv(out/'最终38州模型_S10指标.csv',index=False,
                                      encoding='utf-8-sig',float_format='%.15g')
    print(metrics.to_string(index=False))
    print('S10 metrics saved; direction consistency uses selected iterations only.')


def bootstrap_iteration(iter_idx, X_scaled, y, alpha=LASSO_ALPHA):
    """Run the retained real-label Lasso/post-Lasso OLS/OOB calculation."""
    rng = np.random.RandomState(iter_idx)
    indices = np.arange(len(y))
    train_idx = rng.choice(indices, size=len(y), replace=True)
    oob_idx = np.array(sorted(set(indices) - set(train_idx)))
    if len(oob_idx) < 3:
        return None

    y_use = pd.Series(np.asarray(y), index=indices)
    X_train = X_scaled.iloc[train_idx]
    X_test = X_scaled.iloc[oob_idx]
    y_train = y_use.iloc[train_idx]
    y_test = y_use.iloc[oob_idx]
    selector = Lasso(alpha=alpha, max_iter=5000)
    selector.fit(X_train, y_train)
    selected = X_train.columns[selector.coef_ != 0].tolist()
    result = {"iter": iter_idx, "r2": np.nan, "cor": np.nan, "coefs": {}}

    if selected:
        fitted = sm.OLS(
            y_train, sm.add_constant(X_train[selected])
        ).fit()
        result["coefs"] = fitted.params.drop("const", errors="ignore").to_dict()
        predicted = fitted.predict(
            sm.add_constant(X_test[selected], has_constant="add")
        )
        result["r2"] = r2_score(y_test, predicted)
        if np.std(predicted) > 1e-9 and np.std(y_test) > 1e-9:
            result["cor"] = stats.pearsonr(y_test, predicted)[0]
        else:
            result["cor"] = 0.0
    else:
        predicted = np.full(len(y_test), np.mean(y_train))
        result["r2"] = r2_score(y_test, predicted)
        result["cor"] = 0.0
    return result


def generate_bootstrap(state_file, out, n_iter=N_BOOTSTRAPS, jobs=None):
    """Generate real-label Bootstrap logs using the fixed study cohort.

    This stage evaluates the already specified 38-state, preprocessed sample.
    It does not perform a shuffled-outcome/null-model analysis.
    """
    _, features, _, y, sample, _, z = prepare_state_data(state_file)
    out = prepare_output(out, BOOTSTRAP_OUTPUTS)
    X_scaled = z.loc[sample].reset_index(drop=True)
    y_clean = y.loc[sample].reset_index(drop=True)
    if jobs is None:
        jobs = max(1, (os.cpu_count() or 1) - 1)
    if jobs == 1:
        results = [bootstrap_iteration(i, X_scaled, y_clean) for i in range(n_iter)]
    else:
        from joblib import Parallel, delayed
        results = Parallel(n_jobs=jobs)(
            delayed(bootstrap_iteration)(i, X_scaled, y_clean)
            for i in range(n_iter)
        )
    results = [result for result in results if result is not None]
    if not results:
        raise ValueError("No Bootstrap iteration had at least three OOB states.")

    rows = [{"Iteration": r["iter"], **r["coefs"]} for r in results]
    records = pd.DataFrame(rows).reindex(columns=["Iteration", *features])
    records.to_csv(
        out / BOOTSTRAP_OUTPUTS[0], index=False, float_format="%.6f"
    )
    pd.DataFrame([
        {"Iteration": r["iter"], "OOB_R2": r["r2"], "OOB_Pearson_r": r["cor"]}
        for r in results
    ]).to_csv(out / BOOTSTRAP_OUTPUTS[1], index=False, float_format="%.15g")
    counts = records[features].notna().sum()
    pd.DataFrame({
        "feature": features,
        "selection_count": counts.to_numpy(),
        "selection_frequency": counts.to_numpy() / len(records),
    }).to_csv(out / BOOTSTRAP_OUTPUTS[2], index=False, float_format="%.15g")
    info = {
        "attempted_iterations": n_iter,
        "valid_iterations": len(records),
        "fit_states": sample.tolist(),
        "features": features.tolist(),
        "lasso_alpha": LASSO_ALPHA,
        "CLR_dimensions": 30,
        "pseudocount": EPS,
        "scaling": "38-state StandardScaler",
        "outcome": "asinh(Republican minus Democratic margin)",
        "minimum_OOB_states": 3,
        "iteration_seed": "iteration index",
    }
    (out / BOOTSTRAP_OUTPUTS[3]).write_text(
        json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Saved {len(records)} valid real Bootstrap iterations to {out}")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("final", "bootstrap"), default="final")
    parser.add_argument("--state-features", type=Path)
    parser.add_argument("--bootstrap-log", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--jobs", type=int, help="Parallel workers for the bootstrap stage.")
    args = parser.parse_args()
    state_file = args.state_features or Path(
        project_path("data", "state_level_modeling/state_features.csv")
    )
    if args.stage == "bootstrap":
        out = args.output_dir or Path(
            project_path("outputs", "state_level_modeling/bootstrap")
        )
        generate_bootstrap(state_file, out, jobs=args.jobs)
    else:
        log = args.bootstrap_log or Path(
            project_path("data", "state_level_modeling/Variable_Selection_Raw_Log.csv")
        )
        out = args.output_dir or Path(
            project_path("outputs", "state_level_modeling/regression")
        )
        calculate(state_file, log, out)


if __name__ == "__main__":
    main()
