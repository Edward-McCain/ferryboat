export const statusLabel = {
  scheduled: "в расписании",
  boarding: "посадка",
  departed: "ушёл",
  cancelled: "отменён",
};

export function routeEnds(direction) {
  if (direction === "city_to_island") {
    return ["Город", "Остров"];
  }
  return ["Остров", "Город"];
}
