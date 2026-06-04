export const mockMapData = [];

const baseMockRegionalDetails = {
  "서울": {
    regionName: "서울",
    years: {
      "2026": [
        {
          diseaseName: "코로나19",
          totalCount: 1542,
          demographics: { male: 48, female: 52 },
          ageGroups: [
            { age: "10대 이하", count: 120 },
            { age: "20-30대", count: 540 },
            { age: "40-50대", count: 620 },
            { age: "60대 이상", count: 262 }
          ]
        },
        {
          diseaseName: "독감",
          totalCount: 3200,
          demographics: { male: 50, female: 50 },
          ageGroups: [
            { age: "10대 이하", count: 800 },
            { age: "20-30대", count: 1200 },
            { age: "40-50대", count: 700 },
            { age: "60대 이상", count: 500 }
          ]
        }
      ]
    }
  },
  "경기": {
    regionName: "경기",
    years: {
      "2026": [
        {
          diseaseName: "코로나19",
          totalCount: 2100,
          demographics: { male: 51, female: 49 },
          ageGroups: [
            { age: "10대 이하", count: 200 },
            { age: "20-30대", count: 800 },
            { age: "40-50대", count: 700 },
            { age: "60대 이상", count: 400 }
          ]
        }
      ]
    }
  }
};

export const mockRegionalDetails = new Proxy(baseMockRegionalDetails, {
  get: function(target, prop) {
    // We only care about string properties (regionIds)
    if (typeof prop !== 'string' || prop === '$$typeof') return target[prop];
    
    if (prop in target) {
      return target[prop];
    }
    // Return a graceful dummy structure for missing regions
    return {
      regionName: prop,
      years: {
        "2026": [
          {
            diseaseName: "통계 없음 (AI 분석 지역)",
            totalCount: 0,
            demographics: { male: 50, female: 50 },
            ageGroups: []
          }
        ]
      }
    };
  }
});
