<h1>Project Background</h1>
<p>This project analyzes the underlying market, agronomic, and climatic drivers of U.S. corn prices over a 50-year horizon (1973–2024). Positioned from the perspective of an Agricultural Data Analyst, the objective was to understand structural pricing shifts, market volatility, and supply-demand dynamics by building an automated, enterprise-grade ELT (Extract, Load, Transform) data pipeline.</p>

<p>Insights and recommendations are provided across four key analytical areas:</p>
    <ul>
        <li><strong>Category 1: Market Structural Regime Shifts &amp; Price Dynamics</strong></li>
        <li><strong>Category 2: Supply &amp; Demand Elasticity (Stock-to-Use Ratios)</strong></li>
        <li><strong>Category 3: Agronomic Health &amp; Crop Condition Indices</strong></li>
        <li><strong>Category 4: Climatic Stress &amp; Weather Volatility</strong></li>
    </ul>

<p>The repository contains the end-to-end Python ingestion scripts, Google BigQuery setup, dbt (Data Build Tool) transformations, quality testing protocols, and exploratory data analysis notebooks.</p>

  <ul>
        <li><strong>Data Engineering &amp; Transformations:</strong> Python scripts for dynamic web scraping (Selenium/Requests) and dbt SQL models for cleaning           and feature engineering can be found in the project directory.</li>
        <li><strong>Data Quality &amp; Testing Framework:</strong> Automated dbt test suites verifying schema constraints and domain-specific business rules.</li>
        <li><strong>Exploratory Data Analysis:</strong> Jupyter Notebooks executing statistical profiling, time-series stationarity checks, and correlation                analyses.</li>
  </ul>

<h2>Data Structure &amp; Initial Checks</h2>
<p>The raw data layer is ingested into Google BigQuery (<code>us_corn_data</code>) before being sanitized, transformed, and joined into clean staging models (<code>us_corn_data_transformed</code>) and a final analytical data mart (<code>mart_corn_model_data</code>).</p>

<p>The core architecture consists of 5 staging tables and 1 aggregated model mart:</p>
    <ul>
        <li><code>stg_corn_prices</code>: Monthly U.S. corn market price data (1973–2024) scraped from USDA QuickStats, focused on November end-of-season harvest prices.</li>
        <li><code>stg_corn_supply_demand</code>: Annual macro-level U.S. supply, demand, yield, planted/harvested acreage, usage, and inventory stocks (1973–2024) extracted from USDA WASDE reports.</li>
        <li><code>stg_corn_plantings</code>: Weekly national crop planting progress tracking percentage completion across marketing years (1986–2024).</li>
        <li><code>stg_corn_conditions</code>: Weekly categorical crop ratings (Very Poor, Poor, Fair, Good, Excellent) transformed into a continuous weighted condition index.</li>
        <li><code>stg_corn_climate_features</code>: Daily national precipitation and temperature variables from NOAA, aggregated to capture July heat stress and post-pollination rainfall.</li>
        <li><code>mart_corn_model_data</code>: The central analytical dataset joining all staging tables on <code>year</code>, strictly validated for non-null keys, physics constraints, and complete feature coverage.</li>
    </ul>

<img width="1536" height="1024" alt="pic6" src="https://github.com/user-attachments/assets/d9cc06b3-bbb9-492d-bf30-5c17d8a12cb4" />


<h2>Executive Summary</h2>
<h3>Overview of Findings</h3>
<p>U.S. corn production yield demonstrates long-term technological stability and steady upward growth, yet corn market pricing experienced an abrupt structural regime shift around 2000–2007, driven by policy-mandated ethanol expansion. Market prices demonstrate extreme non-linear sensitivity to inventory tightness (<code>stock_to_use_ratio</code>) and climate shocks during critical growth windows (July pollination).</p>

<p>If a market strategist or agricultural finance director were to take away 3 main insights, they would be:</p>
    <ol>
        <li><strong>Regime Shift:</strong> Post-2007 pricing operates on a significantly higher baseline compared to pre-2007, making historical nominal prices prior to 2007 non-comparable without structural adjustment.</li>
        <li><strong>Asymmetric Risk:</strong> Pricing responds non-linearly to inventory scarcity; when <code>stock_to_use_ratio</code> drops below critical thresholds, price volatility increases exponentially.</li>
        <li><strong>Targeted Weather Impact:</strong> Seasonal climate stress (specifically July heat stress &gt;35°C during silking) impacts end-of-season market pricing far more severely than general annual rainfall metrics.</li>
    </ol>

<img width="1100" height="622" alt="graph6" src="https://github.com/user-attachments/assets/c8fa90dc-79c0-4184-b10a-ec8dcf82dad6" />


<h2>Insights Deep Dive</h2>

<h3>Category 1: Market Structural Regime Shifts &amp; Price Dynamics</h3>
    <ul>
        <li><strong>2007 Structural Break Point.</strong> A prominent structural break in price time-series occurred in 2007. Driven by federal ethanol mandates and expanded renewable fuel standards, corn pricing transitioned from a historic range of $1.50–$3.50/bushel to a higher regime of $3.50–$7.00+/bushel.</li>
        <li><strong>Log-Normal Price Distribution.</strong> Nominal November harvest prices (<code>price_per_bushel</code>) exhibited heavy right-skewness. Applying log-transformation normalized the distribution, enabling robust linear modeling across different pricing regimes.</li>
        <li><strong>Price Volatility vs. Yield Growth.</strong> While technology (genetics, equipment, precision farming) produced a highly predictable, linear upward trend in crop yield per acre (LOESS trend), price volatility expanded significantly due to demand-side shocks.</li>
        <li><strong>Macro Disruption Events.</strong> Major historical price spikes (1983, 1988, 2007, 2012) directly align with explicit macro-exogenous events: the 1983 Payment-in-Kind (PIK) land idling program, the 1988 historic U.S. drought, the 2007 ethanol expansion, and the severe 2012 Midwest drought.</li>
    </ul>

<h3>Category 2: Supply &amp; Demand Elasticity (Stock-to-Use Ratios)</h3>
    <ul>
        <li><strong>Inverse Non-Linear Pricing Relationship.</strong> The <code>stock_to_use_ratio</code> (calculated as <code>ending_stocks / total_usage</code>) serves as the single strongest macro predictor of price. Lower inventory ratios reliably correlate with elevated prices.</li>
        <li><strong>Regime Sensitivity Difference.</strong> In the pre-ethanol era, inventory fluctuations produced tight, predictable price ranges. In the post-ethanol era, identical stock-to-use ratios correspond to significantly higher price levels due to elevated baseline demand.</li>
        <li><strong>Buffer Capacity Constraints.</strong> When ending stocks drop relative to usage, market buffer capacity deteriorates, magnifying price reactions to even minor yield underperformances.</li>
        <li><strong>Acreage Expansion Dynamics.</strong> Sharply rising prices in peak years (e.g., 2007) drove immediate acreage expansions in subsequent planting seasons, proving that supply response is highly elastic to price signals following deficit years.</li>
    </ul>

<h3>Category 3: Agronomic Health &amp; Crop Condition Indices</h3>
<ul>
        <li><strong>Weighted Crop Condition Metric.</strong> By transforming raw categorical USDA ratings into a weighted continuous scale (<code>avg_condition_pollination_index</code>), crop health during the key pollination window was quantitatively modeled against end-of-season price.</li>
        <li><strong>Inverse Condition-to-Price Response.</strong> Higher pollination health scores strongly correlate with lower November prices, as superior crop health signals high realized yield and market supply.</li>
        <li><strong>Early Warning Indicator.</strong> Crop condition indices measured during summer weeks serve as an early reliable proxy for harvest prices months before WASDE production finalizations.</li>
        <li><strong>Drought Resilience Shift.</strong> Comparison of severe drought years (1988 vs. 2012) reveals that modern seed hybrids maintain higher baseline crop condition ratings under adverse conditions than earlier genetic variants.</li>
    </ul>

<h3>Category 4: Climatic Stress &amp; Weather Volatility</h3>
    <ul>
        <li><strong>July Temperature Threshold Stress.</strong> Heat stress counted during the critical July silking window (<code>temp_stress_july_count</code> &gt; 35°C) exhibits a direct positive correlation with harvest prices; excessive heat impairs fertilization, reducing overall yields.</li>
        <li><strong>Precipitation Timing Sensitivity.</strong> Total annual rainfall is a weak predictor of yield and price compared to targeted timing metrics (<code>post_pollination_rain</code> and <code>rainfall_effectiveness_index</code>).</li>
        <li><strong>The 2012 Climate Shock.</strong> The 2012 drought registered extreme values across heat stress counts and low crop condition index scores, directly driving November prices to record historical highs (~$7.00/bushel).</li>
        <li><strong>Rebound Dynamics (2012–2013).</strong> Severe climate shocks in 2012 were immediately followed by a sharp yield and stock recovery in 2013, demonstrating strong physical and supply recovery capacity across U.S. agricultural infrastructure.</li>
    </ul>

<h2>Recommendations</h2>
<p>Based on the empirical insights derived from the pipeline, the following actions are recommended for commodities analysts, risk managers, and decision-makers:</p>
    <ul>
        <li><strong>Incorporate Structural Regime Splits in Forecasting Models.</strong> Avoid training price models on full 1973–2024 unadjusted historical data. <strong>Segment training sets into pre- and post-2007 regimes or include structural break dummy variables to prevent baseline price underestimation.</strong></li>
        <li><strong>Monitor Inventory Ratios over Absolute Production Volumes.</strong> Do not rely solely on gross production figures. <strong>Prioritize tracking <code>stock_to_use_ratio</code> threshold dips below critical points to hedge against exponential price volatility.</strong></li>
        <li><strong>Focus Climate Monitoring on Key Growth Windows.</strong> General seasonal rainfall metrics provide weak predictive power. <strong>Deploy localized climate tracking specifically targeting July heat stress days (&gt;35°C) and post-pollination rainfall.</strong></li>
        <li><strong>Leverage dbt Shift-Left Data Quality Assurance.</strong> Implement domain-specific "physics" testing rules on ingested data tables. <strong>Constrain crop condition indices (1–5) and non-negative rainfall values at the staging layer to eliminate data errors prior to running downstream statistical models.</strong></li>
        <li><strong>Automate Dashboard and Pipeline Ingestion.</strong> Expand the Python orchestrator into a cloud-native schedule. <strong>Connect BI tools directly to the BigQuery <code>mart_corn_model_data</code> layer for real-time risk monitoring.</strong></li>
    </ul>

<h2>Assumptions and Caveats</h2>
<p>Throughout the pipeline construction and analysis, several data processing assumptions and physical limitations were established:</p>
    <ul>
        <li><strong>Marketing Year Definition.</strong> Annual metrics follow the USDA agricultural marketing year standard rather than calendar years, aligning harvest periods with ending stock computations.</li>
        <li><strong>Data Granularity Normalization.</strong> Crop condition and progress datasets natively collected at weekly intervals were aggregated to annual features linked to specific crop phenology stages (e.g., 50% planting day of year).</li>
        <li><strong>Missing Feature Exclusion.</strong> Years with missing or incomplete agronomic/climatic variable coverage were excluded from the final joined mart model using inner-join constraints to preserve statistical integrity.</li>
        <li><strong>Exclusion of Forecast Estimates.</strong> To maintain deterministic historical accuracy, USDA WASDE forward-looking estimate years (such as 2025 estimates) were explicitly filtered out during ingestion.</li>
        <li><strong>GCP Sandbox Restrictions.</strong> Compute environments utilized Google Cloud BigQuery Sandbox configurations; large-scale transformations were optimized within storage quotas without loss of operational fidelity.</li>
    </ul>
