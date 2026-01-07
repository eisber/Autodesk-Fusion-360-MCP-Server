/**
 * Measurement tools for Fusion 360 MCP Server.
 */

import { z } from "zod";
import { createPostTool, createGetTool, ToolResult } from "./base.js";

// Zod schemas
export const measureDistanceSchema = z.object({
  entity1_type: z
    .string()
    .describe("Type: 'face', 'edge', 'vertex', or 'body'"),
  entity1_index: z.number().describe("Index of first entity"),
  entity2_type: z
    .string()
    .describe("Type: 'face', 'edge', 'vertex', or 'body'"),
  entity2_index: z.number().describe("Index of second entity"),
  body1_index: z.number().default(0).describe("Body index for first entity"),
  body2_index: z.number().default(0).describe("Body index for second entity"),
});

export const measureAngleSchema = z.object({
  entity1_type: z.string().describe("Type: 'face' or 'edge'"),
  entity1_index: z.number().describe("Index of first entity"),
  entity2_type: z.string().describe("Type: 'face' or 'edge'"),
  entity2_index: z.number().describe("Index of second entity"),
  body1_index: z.number().default(0).describe("Body index for first entity"),
  body2_index: z.number().default(0).describe("Body index for second entity"),
});

export const measureAreaSchema = z.object({
  face_index: z.number().describe("Index of the face"),
  body_index: z.number().default(0).describe("Index of the body"),
});

export const measureVolumeSchema = z.object({
  body_index: z.number().default(0).describe("Index of the body"),
});

export const measureEdgeLengthSchema = z.object({
  edge_index: z.number().describe("Index of the edge"),
  body_index: z.number().default(0).describe("Index of the body"),
});

export const measureBodyPropertiesSchema = z.object({
  body_index: z.number().default(0).describe("Index of the body"),
});

export const measurePointToPointSchema = z.object({
  point1: z.array(z.number()).length(3).describe("[x, y, z] of first point"),
  point2: z.array(z.number()).length(3).describe("[x, y, z] of second point"),
});

export const getEdgesInfoSchema = z.object({
  body_index: z.number().default(0).describe("Index of the body to inspect"),
});

export const getVerticesInfoSchema = z.object({
  body_index: z.number().default(0).describe("Index of the body to inspect"),
});

// Tool implementations
const _measureDistance = createPostTool("measure_distance");
const _measureAngle = createPostTool("measure_angle");
const _measureArea = createPostTool("measure_area");
const _measureVolume = createPostTool("measure_volume");
const _measureEdgeLength = createPostTool("measure_edge_length");
const _measureBodyProperties = createPostTool("measure_body_properties");
const _measurePointToPoint = createPostTool("measure_point_to_point");
const _getEdgesInfo = createGetTool("edges_info");
const _getVerticesInfo = createGetTool("vertices_info");

// Exported functions

/**
 * Measure the minimum distance between two entities.
 */
export async function measure_distance(
  entity1_type: string,
  entity1_index: number,
  entity2_type: string,
  entity2_index: number,
  body1_index: number = 0,
  body2_index: number = 0
): Promise<ToolResult> {
  return _measureDistance({
    entity1_type,
    entity1_index,
    entity2_type,
    entity2_index,
    body1_index,
    body2_index,
  });
}

/**
 * Measure the angle between two planar faces or linear edges.
 */
export async function measure_angle(
  entity1_type: string,
  entity1_index: number,
  entity2_type: string,
  entity2_index: number,
  body1_index: number = 0,
  body2_index: number = 0
): Promise<ToolResult> {
  return _measureAngle({
    entity1_type,
    entity1_index,
    entity2_type,
    entity2_index,
    body1_index,
    body2_index,
  });
}

/**
 * Measure the area of a specific face.
 */
export async function measure_area(
  face_index: number,
  body_index: number = 0
): Promise<ToolResult> {
  return _measureArea({ face_index, body_index });
}

/**
 * Measure the volume of a body.
 */
export async function measure_volume(
  body_index: number = 0
): Promise<ToolResult> {
  return _measureVolume({ body_index });
}

/**
 * Measure the length of a specific edge.
 */
export async function measure_edge_length(
  edge_index: number,
  body_index: number = 0
): Promise<ToolResult> {
  return _measureEdgeLength({ edge_index, body_index });
}

/**
 * Get comprehensive physical properties of a body.
 */
export async function measure_body_properties(
  body_index: number = 0
): Promise<ToolResult> {
  return _measureBodyProperties({ body_index });
}

/**
 * Measure the distance between two specific 3D points.
 */
export async function measure_point_to_point(
  point1: number[],
  point2: number[]
): Promise<ToolResult> {
  return _measurePointToPoint({ point1, point2 });
}

/**
 * Get detailed edge information for a body.
 */
export async function get_edges_info(
  body_index: number = 0
): Promise<ToolResult> {
  return _getEdgesInfo({ body_index });
}

/**
 * Get detailed vertex information for a body.
 */
export async function get_vertices_info(
  body_index: number = 0
): Promise<ToolResult> {
  return _getVerticesInfo({ body_index });
}
