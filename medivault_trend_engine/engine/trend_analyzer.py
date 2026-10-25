"""
Clinical Trend Analyzer for Medical Trend Analysis Engine.
Analyzes chronological biomarker measurements, identifies improvement and deterioration,
computes confidence scores, and builds grounded citations.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from medivault_trend_engine.schemas.trend_schema import (
    BiomarkerMeasurement,
    TrendDirection,
    AlertSeverity,
    ReportCitation,
    ImprovementSummary,
    DeteriorationAlert,
    MarkerTrendResult,
    TrendGraphData,
    DoctorReadySummary,
    PatientTrendAnalysisResponse,
)
from medivault_trend_engine.biomarkers.biomarker_catalog import (
    resolve_biomarker,
    DesiredDirection,
    BiomarkerProfile,
    CATALOG,
)
from medivault_trend_engine.visualizer.graph_generator import TrendGraphGenerator

class ClinicalTrendAnalyzer:
    """
    Evaluates historical lab reports, derives trends, alerts on deterioration,
    and produces verified doctor-ready summaries with citations.
    """

    def __init__(self, graph_generator: Optional[TrendGraphGenerator] = None):
        self.graph_generator = graph_generator or TrendGraphGenerator()

    def analyze_patient_trends(
        self,
        patient_id: str,
        measurements: List[BiomarkerMeasurement],
        target_biomarkers: Optional[List[str]] = None,
    ) -> PatientTrendAnalysisResponse:
        """
        Executes longitudinal analysis across patient biomarker measurements.
        """
        if not measurements:
            # Zero values case
            doc_summary = DoctorReadySummary(
                headline=f"No Historical Data Available for Patient {patient_id}",
                patient_id=patient_id,
                monitoring_interval="None",
                biomarkers_reviewed=[],
                clinical_trajectory="No longitudinal laboratory records found.",
                priority_action_items=["Obtain baseline lab tests."],
                citations=[],
            )
            return PatientTrendAnalysisResponse(
                patient_id=patient_id,
                summary="No clinical biomarker measurements available for trend analysis.",
                explanation="I could not find that information in your medical records.",
                confidence_score=0.0,
                marker_trends={},
                trend_graphs=[],
                improvement_summaries=[],
                deterioration_alerts=[],
                doctor_ready_summary=doc_summary,
                citations=[],
            )

        # 1. Group measurements by canonical biomarker
        grouped: Dict[str, List[BiomarkerMeasurement]] = {}
        for m in measurements:
            profile = resolve_biomarker(m.test_name)
            name = profile.canonical_name if profile else m.test_name
            if target_biomarkers and name not in target_biomarkers:
                continue
            grouped.setdefault(name, []).append(m)

        all_citations_map: Dict[Tuple[str, int, str], ReportCitation] = {}
        marker_trends: Dict[str, MarkerTrendResult] = {}
        trend_graphs: List[TrendGraphData] = []
        improvements: List[ImprovementSummary] = []
        deteriorations: List[DeteriorationAlert] = []

        # 2. Analyze each biomarker chronologically
        for marker_name, points in grouped.items():
            # Sort chronologically by date
            sorted_pts = sorted(points, key=lambda x: x.report_date)
            profile = resolve_biomarker(marker_name)

            for p in sorted_pts:
                all_citations_map[(p.report_name, p.page_number, p.report_date)] = ReportCitation(
                    report_name=p.report_name,
                    page_number=p.page_number,
                    report_date=p.report_date,
                    document_id=p.document_id,
                )

            marker_res = self._analyze_single_marker(marker_name, sorted_pts, profile)
            marker_trends[marker_name] = marker_res

            if marker_res.graph:
                trend_graphs.append(marker_res.graph)
            if marker_res.improvement_summary:
                improvements.append(marker_res.improvement_summary)
            if marker_res.deterioration_alert:
                deteriorations.append(marker_res.deterioration_alert)

        all_citations = list(all_citations_map.values())

        # 3. Compute deterministic confidence score
        confidence = self._compute_confidence(grouped, measurements)

        # 4. Generate structured Doctor-Ready Summary
        doctor_summary = self._build_doctor_summary(patient_id, marker_trends, improvements, deteriorations, all_citations)

        # 5. Generate overall summary and patient-facing explanation
        summary, explanation = self._build_narratives(marker_trends, improvements, deteriorations)

        return PatientTrendAnalysisResponse(
            patient_id=patient_id,
            summary=summary,
            explanation=explanation,
            confidence_score=confidence,
            marker_trends=marker_trends,
            trend_graphs=trend_graphs,
            improvement_summaries=improvements,
            deterioration_alerts=deteriorations,
            doctor_ready_summary=doctor_summary,
            citations=all_citations,
        )

    def _analyze_single_marker(
        self,
        marker_name: str,
        points: List[BiomarkerMeasurement],
        profile: Optional[BiomarkerProfile],
    ) -> MarkerTrendResult:
        citations = [
            ReportCitation(
                report_name=p.report_name,
                page_number=p.page_number,
                report_date=p.report_date,
                document_id=p.document_id,
            )
            for p in points
        ]

        if len(points) < 2:
            single = points[0]
            is_norm = True
            if profile:
                is_norm = profile.normal_min <= single.value <= profile.normal_max
            return MarkerTrendResult(
                biomarker_name=marker_name,
                data_points=points,
                direction=TrendDirection.INSUFFICIENT_DATA,
                delta_absolute=0.0,
                delta_percent=0.0,
                is_currently_normal=is_norm,
                improvement_summary=None,
                deterioration_alert=None,
                graph=None,
                citations=citations,
            )

        baseline = points[0]
        latest = points[-1]
        delta_abs = round(latest.value - baseline.value, 2)
        delta_pct = round(((latest.value - baseline.value) / baseline.value) * 100, 2) if baseline.value != 0 else 0.0

        is_currently_normal = True
        normal_min = profile.normal_min if profile else None
        normal_max = profile.normal_max if profile else None
        if normal_min is not None and normal_max is not None:
            is_currently_normal = normal_min <= latest.value <= normal_max

        direction, improvement, deterioration = self._evaluate_clinical_trajectory(
            marker_name=marker_name,
            baseline=baseline,
            latest=latest,
            delta_abs=delta_abs,
            delta_pct=delta_pct,
            profile=profile,
            citations=citations,
        )

        graph = self.graph_generator.generate_graph(
            biomarker_name=marker_name,
            unit=latest.unit,
            measurements=points,
            normal_min=normal_min,
            normal_max=normal_max,
            direction=direction,
        )

        return MarkerTrendResult(
            biomarker_name=marker_name,
            data_points=points,
            direction=direction,
            delta_absolute=delta_abs,
            delta_percent=delta_pct,
            is_currently_normal=is_currently_normal,
            improvement_summary=improvement,
            deterioration_alert=deterioration,
            graph=graph,
            citations=citations,
        )

    def _evaluate_clinical_trajectory(
        self,
        marker_name: str,
        baseline: BiomarkerMeasurement,
        latest: BiomarkerMeasurement,
        delta_abs: float,
        delta_pct: float,
        profile: Optional[BiomarkerProfile],
        citations: List[ReportCitation],
    ) -> Tuple[TrendDirection, Optional[ImprovementSummary], Optional[DeteriorationAlert]]:
        desired = profile.desired_direction if profile else DesiredDirection.LOWER_IS_BETTER
        sig_threshold = profile.significant_delta_pct if profile else 5.0

        improvement: Optional[ImprovementSummary] = None
        deterioration: Optional[DeteriorationAlert] = None
        direction = TrendDirection.STABLE

        # Within +/- significant threshold is stable
        if abs(delta_pct) < sig_threshold:
            return TrendDirection.STABLE, None, None

        if desired == DesiredDirection.LOWER_IS_BETTER:
            if delta_pct <= -sig_threshold:
                direction = TrendDirection.IMPROVING
                improvement = ImprovementSummary(
                    biomarker_name=marker_name,
                    baseline_date=baseline.report_date,
                    baseline_value=baseline.value,
                    latest_date=latest.report_date,
                    latest_value=latest.value,
                    unit=latest.unit,
                    delta_absolute=delta_abs,
                    delta_percent=delta_pct,
                    clinical_significance=(
                        f"{marker_name} improved by {abs(delta_abs)} {latest.unit} ({abs(delta_pct)}% reduction), "
                        f"moving from {baseline.value} {baseline.unit} on {baseline.report_date} "
                        f"to {latest.value} {latest.unit} on {latest.report_date}."
                    ),
                    citations=citations,
                )
            elif delta_pct >= sig_threshold:
                direction = TrendDirection.DETERIORATING
                severity = AlertSeverity.WARNING
                if profile and profile.critical_high and latest.value >= profile.critical_high:
                    severity = AlertSeverity.CRITICAL

                deterioration = DeteriorationAlert(
                    biomarker_name=marker_name,
                    severity=severity,
                    alert_message=f"Deterioration Alert: {marker_name} increased by {delta_abs} {latest.unit} ({delta_pct}%)",
                    baseline_date=baseline.report_date,
                    baseline_value=baseline.value,
                    latest_date=latest.report_date,
                    latest_value=latest.value,
                    unit=latest.unit,
                    delta_absolute=delta_abs,
                    delta_percent=delta_pct,
                    clinical_risk=(
                        f"Worsening trajectory: {marker_name} elevated from {baseline.value} to {latest.value} {latest.unit}. "
                        "Discuss clinical management and lifestyle factors with your physician."
                    ),
                    citations=citations,
                )

        elif desired == DesiredDirection.HIGHER_IS_BETTER:
            if delta_pct >= sig_threshold:
                direction = TrendDirection.IMPROVING
                improvement = ImprovementSummary(
                    biomarker_name=marker_name,
                    baseline_date=baseline.report_date,
                    baseline_value=baseline.value,
                    latest_date=latest.report_date,
                    latest_value=latest.value,
                    unit=latest.unit,
                    delta_absolute=delta_abs,
                    delta_percent=delta_pct,
                    clinical_significance=f"{marker_name} increased by {delta_abs} {latest.unit} ({delta_pct}%), demonstrating functional recovery.",
                    citations=citations,
                )
            elif delta_pct <= -sig_threshold:
                direction = TrendDirection.DETERIORATING
                severity = AlertSeverity.WARNING
                if profile and profile.critical_low and latest.value <= profile.critical_low:
                    severity = AlertSeverity.CRITICAL

                deterioration = DeteriorationAlert(
                    biomarker_name=marker_name,
                    severity=severity,
                    alert_message=f"Deterioration Alert: {marker_name} dropped by {abs(delta_abs)} {latest.unit} ({abs(delta_pct)}%)",
                    baseline_date=baseline.report_date,
                    baseline_value=baseline.value,
                    latest_date=latest.report_date,
                    latest_value=latest.value,
                    unit=latest.unit,
                    delta_absolute=delta_abs,
                    delta_percent=delta_pct,
                    clinical_risk=f"Significant functional decline in {marker_name} from {baseline.value} to {latest.value} {latest.unit}.",
                    citations=citations,
                )

        else: # WITHIN_RANGE_IS_BETTER
            norm_mid = ((profile.normal_min + profile.normal_max) / 2.0) if profile else baseline.value
            baseline_dist = abs(baseline.value - norm_mid)
            latest_dist = abs(latest.value - norm_mid)

            if latest_dist < baseline_dist:
                direction = TrendDirection.IMPROVING
                improvement = ImprovementSummary(
                    biomarker_name=marker_name,
                    baseline_date=baseline.report_date,
                    baseline_value=baseline.value,
                    latest_date=latest.report_date,
                    latest_value=latest.value,
                    unit=latest.unit,
                    delta_absolute=delta_abs,
                    delta_percent=delta_pct,
                    clinical_significance=f"{marker_name} converged toward healthy normal reference range.",
                    citations=citations,
                )
            else:
                direction = TrendDirection.DETERIORATING
                deterioration = DeteriorationAlert(
                    biomarker_name=marker_name,
                    severity=AlertSeverity.WARNING,
                    alert_message=f"{marker_name} deviated further from normal target range.",
                    baseline_date=baseline.report_date,
                    baseline_value=baseline.value,
                    latest_date=latest.report_date,
                    latest_value=latest.value,
                    unit=latest.unit,
                    delta_absolute=delta_abs,
                    delta_percent=delta_pct,
                    clinical_risk=f"{marker_name} shifted from {baseline.value} to {latest.value} {latest.unit}.",
                    citations=citations,
                )

        return direction, improvement, deterioration

    def _compute_confidence(
        self,
        grouped: Dict[str, List[BiomarkerMeasurement]],
        all_measurements: List[BiomarkerMeasurement],
    ) -> float:
        """
        Computes deterministic confidence score based on:
        - Total sample count (longitudinal depth)
        - Metadata integrity (date, page, report name)
        """
        if not all_measurements:
            return 0.0

        max_pts = max([len(pts) for pts in grouped.values()])
        if max_pts >= 3:
            score = 0.95
        elif max_pts == 2:
            score = 0.82
        else:
            score = 0.45

        # Penalty if dates missing or invalid
        for m in all_measurements:
            if not m.report_date or not m.report_name:
                score -= 0.15

        return round(max(0.1, min(0.99, score)), 2)

    def _build_doctor_summary(
        self,
        patient_id: str,
        marker_trends: Dict[str, MarkerTrendResult],
        improvements: List[ImprovementSummary],
        deteriorations: List[DeteriorationAlert],
        citations: List[ReportCitation],
    ) -> DoctorReadySummary:
        dates = sorted({c.report_date for c in citations if c.report_date})
        interval = f"{dates[0]} to {dates[-1]}" if len(dates) >= 2 else (dates[0] if dates else "Single observation")

        action_items = []
        if deteriorations:
            for d in deteriorations:
                action_items.append(f"Review worsening trend in {d.biomarker_name} ({d.baseline_value} -> {d.latest_value} {d.unit}).")
        if improvements:
            for imp in improvements:
                action_items.append(f"Reinforce favorable progress in {imp.biomarker_name} ({imp.baseline_value} -> {imp.latest_value} {imp.unit}).")
        if not action_items:
            action_items.append("Continue current monitoring protocol; all tracked biomarkers remain stable.")

        trajectory_words = []
        if improvements:
            trajectory_words.append(f"{len(improvements)} marker(s) demonstrated clinical improvement")
        if deteriorations:
            trajectory_words.append(f"{len(deteriorations)} marker(s) flagged for deterioration")
        if not trajectory_words:
            trajectory_words.append("Biomarkers showed stable longitudinal values")

        trajectory = "; ".join(trajectory_words) + "."

        return DoctorReadySummary(
            headline=f"Clinical Biomarker Trend Briefing - Patient {patient_id}",
            patient_id=patient_id,
            monitoring_interval=interval,
            biomarkers_reviewed=list(marker_trends.keys()),
            clinical_trajectory=trajectory,
            priority_action_items=action_items,
            citations=citations,
        )

    def _build_narratives(
        self,
        marker_trends: Dict[str, MarkerTrendResult],
        improvements: List[ImprovementSummary],
        deteriorations: List[DeteriorationAlert],
    ) -> Tuple[str, str]:
        summary_lines = []
        if improvements:
            names = ", ".join([f"{i.biomarker_name} ({i.delta_percent}%)" for i in improvements])
            summary_lines.append(f"Favorable clinical improvement observed in {names}.")
        if deteriorations:
            names = ", ".join([f"{d.biomarker_name} (+{d.delta_percent}%)" for d in deteriorations])
            summary_lines.append(f"Attention required: Deterioration alerts generated for {names}.")
        if not summary_lines:
            summary_lines.append("Tracked biomarkers demonstrate stable historical values across recorded reports.")

        summary = " ".join(summary_lines)

        explanation_lines = [
            "This longitudinal trend analysis compares verified historical laboratory values from your medical records without extrapolation:",
        ]
        for name, trend in marker_trends.items():
            pts_str = " -> ".join([f"{p.value} {p.unit} ({p.report_date})" for p in trend.data_points])
            status = "Within normal reference range" if trend.is_currently_normal else "Outside target range"
            explanation_lines.append(
                f"- **{name}**: {pts_str} | Status: {trend.direction.value} ({status})."
            )

        explanation = "\n".join(explanation_lines)
        return summary, explanation
