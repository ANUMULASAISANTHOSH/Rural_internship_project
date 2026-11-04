"""
AQUILA Phase 4 - Explainable Route Recommendation Service
Synthesizes transparent, human-readable explanations comparing shortest (distance-optimal)
and lowest-risk (safety-optimal) routes during urban flood conditions.
"""

from typing import Dict, Any


class RouteExplanationService:
    @staticmethod
    def explain_route_comparison(
        shortest_route: Dict[str, Any],
        lowest_risk_route: Dict[str, Any],
        lambda_param: float = 3.0
    ) -> Dict[str, Any]:
        """
        Analyzes trade-offs between shortest and lowest-risk routes.
        Returns a structured summary and human-readable operational justification.
        """
        if not shortest_route.get("found") or not lowest_risk_route.get("found"):
            return {
                "has_recommendation": False,
                "preferred_route": "NONE",
                "explanation_summary": "Unable to calculate alternative routes due to network severance or unreachable destination.",
                "distance_delta_meters": 0.0,
                "distance_delta_pct": 0.0,
                "risk_reduction_pct": 0.0,
                "avoided_high_risk_segments": 0,
                "avoided_incident_segments": 0,
                "scientific_disclaimer": "Routing relies on empirical multi-criteria risk scoring and does not guarantee physical road passability."
            }

        d_short = shortest_route["total_distance_meters"]
        d_risk = lowest_risk_route["total_distance_meters"]
        r_short = shortest_route["average_risk_score"]
        r_risk = lowest_risk_route["average_risk_score"]

        high_short = shortest_route.get("high_risk_segment_count", 0)
        high_risk = lowest_risk_route.get("high_risk_segment_count", 0)

        inc_short = shortest_route.get("incident_affected_segment_count", 0)
        inc_risk = lowest_risk_route.get("incident_affected_segment_count", 0)

        dis_short = shortest_route.get("disruption_affected_segment_count", 0)
        dis_risk = lowest_risk_route.get("disruption_affected_segment_count", 0)

        dist_diff_m = round(d_risk - d_short, 1)
        dist_diff_pct = round((dist_diff_m / max(0.1, d_short)) * 100.0, 1) if d_short > 0 else 0.0
        risk_reduction = round(r_short - r_risk, 1)
        risk_reduction_pct = round((risk_reduction / max(0.1, r_short)) * 100.0, 1) if r_short > 0 else 0.0

        avoided_high = max(0, high_short - high_risk)
        avoided_inc = max(0, inc_short - inc_risk)
        avoided_dis = max(0, dis_short - dis_risk)

        # Logic for route preference
        is_identical = (dist_diff_m <= 10.0 and abs(r_short - r_risk) < 0.5 and avoided_inc == 0 and avoided_dis == 0)

        if is_identical:
            preferred = "SHORTEST"
            summary = (
                f"The shortest path ({d_short:.0f} m) is already safety-optimal. It navigates low-to-moderate "
                f"risk corridors (average risk {r_short:.1f}/100) with zero active flood disruptions or incident "
                f"intersections, so no detour penalty is incurred."
            )
        elif avoided_dis > 0 or avoided_inc > 0:
            preferred = "LOWEST_RISK"
            hazards_avoided = []
            if avoided_dis > 0:
                hazards_avoided.append(f"{avoided_dis} simulated road disruption zone(s)")
            if avoided_inc > 0:
                hazards_avoided.append(f"{avoided_inc} active flood incident corridor(s)")
            hazard_str = " and ".join(hazards_avoided)

            summary = (
                f"The lowest-risk route is recommended. It requires a {dist_diff_pct:.1f}% distance detour "
                f"(+{dist_diff_m:.0f} m, total {d_risk:.0f} m vs {d_short:.0f} m) but successfully bypasses {hazard_str}, "
                f"reducing overall flood hazard exposure by {risk_reduction_pct:.1f}% (from {r_short:.1f} to {r_risk:.1f}/100)."
            )
        elif r_short >= 60.0 and r_risk < 50.0:
            preferred = "LOWEST_RISK"
            summary = (
                f"The lowest-risk route is recommended. Although {dist_diff_pct:.1f}% longer (+{dist_diff_m:.0f} m), "
                f"it avoids low-lying drainage depressions, lowering route vulnerability from {r_short:.1f} to {r_risk:.1f}/100 "
                f"and bypassing {avoided_high} high-vulnerability segment(s)."
            )
        elif dist_diff_pct > 35.0 and inc_short == 0 and dis_short == 0:
            preferred = "SHORTEST"
            summary = (
                f"The shortest route is favored for operational urgency. The lowest-risk alternative requires an "
                f"excessive detour of {dist_diff_pct:.1f}% (+{dist_diff_m:.0f} m) without bypassing any confirmed "
                f"incident blockages."
            )
        else:
            preferred = "LOWEST_RISK"
            summary = (
                f"The lowest-risk route is recommended for precautionary emergency navigation. It is {dist_diff_pct:.1f}% "
                f"longer ({d_risk:.0f} m vs {d_short:.0f} m) while lowering average terrain vulnerability from "
                f"{r_short:.1f} to {r_risk:.1f}/100."
            )

        return {
            "has_recommendation": True,
            "preferred_route": preferred,
            "explanation_summary": summary,
            "is_identical_route": is_identical,
            "shortest_distance_meters": d_short,
            "lowest_risk_distance_meters": d_risk,
            "distance_delta_meters": dist_diff_m,
            "distance_delta_pct": dist_diff_pct,
            "shortest_average_risk": r_short,
            "lowest_risk_average_risk": r_risk,
            "risk_reduction_absolute": risk_reduction,
            "risk_reduction_pct": max(0.0, risk_reduction_pct),
            "avoided_high_risk_segments": avoided_high,
            "avoided_incident_segments": avoided_inc,
            "avoided_disruption_segments": avoided_dis,
            "lambda_risk_weight": lambda_param,
            "scientific_disclaimer": (
                "Recommendation is generated by AQUILA's decision-support heuristic (λ="
                f"{lambda_param}). It evaluates relative multi-factor vulnerability and incident proximity; "
                "it does not certify physical flood water depth or real-time vehicular passability."
            )
        }


route_explanation_service = RouteExplanationService()

