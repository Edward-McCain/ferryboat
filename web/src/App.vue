<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";

import { createCrossing, listCrossings, removeCrossing, setStatus, updateCrossing } from "./api";
import CrossingForm from "./components/CrossingForm.vue";
import CrossingList from "./components/CrossingList.vue";
import NextPlate from "./components/NextPlate.vue";

const crossings = ref([]);
const loading = ref(true);
const loadError = ref("");
const actionError = ref("");
const formError = ref("");
const pending = ref(false);
const mode = ref("list");
const editing = ref(null);

const dateLabel = new Intl.DateTimeFormat("ru-RU", {
  day: "numeric",
  month: "long",
}).format(new Date());

const nextCrossing = computed(() => {
  // Посадка важнее более раннего рейса, который ещё просто стоит в расписании.
  const boarding = crossings.value.find((item) => item.status === "boarding");
  if (boarding) {
    return boarding;
  }
  return crossings.value.find((item) => item.status === "scheduled") ?? null;
});

async function reload() {
  crossings.value = await listCrossings();
}

async function run(action, onError) {
  if (pending.value) {
    return;
  }
  pending.value = true;
  actionError.value = "";
  try {
    await action();
    await reload();
  } catch (error) {
    onError(error instanceof Error ? error.message : "Лист не ответил.");
  } finally {
    pending.value = false;
  }
}

function startCreate() {
  editing.value = null;
  formError.value = "";
  mode.value = "create";
}

function startEdit(item) {
  editing.value = item;
  formError.value = "";
  mode.value = "edit";
}

function closeForm() {
  mode.value = "list";
  formError.value = "";
  editing.value = null;
}

function save(payload) {
  formError.value = "";
  const current = editing.value;
  return run(
    () => (current ? updateCrossing(current.id, payload) : createCrossing(payload)),
    (message) => {
      formError.value = message;
    },
  ).then(() => {
    if (!formError.value) {
      closeForm();
    }
  });
}

function changeStatus(id, status) {
  return run(
    () => setStatus(id, status),
    (message) => {
      actionError.value = message;
    },
  );
}

function remove(id) {
  return run(
    () => removeCrossing(id),
    (message) => {
      actionError.value = message;
    },
  );
}

function onKey(event) {
  if (event.key === "Escape" && mode.value !== "list") {
    closeForm();
  }
}

onMounted(async () => {
  window.addEventListener("keydown", onKey);
  try {
    await reload();
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : "Лист не ответил.";
  } finally {
    loading.value = false;
  }
});

onUnmounted(() => {
  window.removeEventListener("keydown", onKey);
});
</script>

<template>
  <div class="desk">
    <header class="top">
      <div>
        <h1>Рейс</h1>
        <p class="lede">Паром на остров. Лист этой ночи, {{ dateLabel }}.</p>
      </div>
      <button v-if="mode === 'list'" type="button" class="solid" @click="startCreate">
        Добавить рейс
      </button>
    </header>

    <div class="layout">
      <NextPlate :crossing="nextCrossing" :loading="loading" :failed="Boolean(loadError)" />
      <section class="sheet">
        <p v-if="loading" class="empty">Открываю лист.</p>
        <p v-else-if="loadError" class="alert" role="alert">{{ loadError }}</p>
        <template v-else>
          <CrossingForm
            v-if="mode !== 'list'"
            :crossing="editing"
            :error="formError"
            :pending="pending"
            @save="save"
            @close="closeForm"
          />
          <template v-else>
            <p v-if="actionError" class="alert" role="alert">{{ actionError }}</p>
            <CrossingList
              :crossings="crossings"
              :pending="pending"
              @edit="startEdit"
              @status="changeStatus($event.id, $event.status)"
              @remove="remove"
            />
          </template>
        </template>
      </section>
    </div>
  </div>
</template>
